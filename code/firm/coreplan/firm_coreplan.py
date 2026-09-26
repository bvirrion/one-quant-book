"""firm.coreplan -- core placement plan (build of One Quant Book 13, chapter 4).

Reads a machine's topology from sysfs (or a fixture tree with the same layout), places the hot-path threads of a
trading process on the NUMA node that holds its network card, one physical core each with the hyper-threading sibling
left idle, and gives everything else (interrupts, the kernel, logging, monitoring) to housekeeping CPUs. The plan is
data: chapter 9's `firm.affinity` pins threads from it and chapter 13's `firm.tuneaudit` checks a host against it.

API (stable):
    read_topology(root="/") -> Topology           cpus {cpu: Cpu(package, core, node, siblings)}, nodes, cards
    Topology.card_for(ifname) -> Card             the PCI device behind a network interface
    plan(topo, ifname, hot=("feed", "strategy", "gateway"), cold=("logger",)) -> Plan
    check(plan, topo) -> list[str]                violated rules (empty when the plan is sound)
    remote_penalty_ns(lines_in, lines_out, local_ns, remote_ns) -> float
    write_plan(plan, path) / read_plan(path) -> {role: cpu}   the text file firm.affinity reads: "role cpu" per line
"""
import pathlib
from dataclasses import dataclass, field


def parse_cpulist(text):
    out = []
    for part in text.strip().split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            out += range(int(a), int(b) + 1)
        else:
            out.append(int(part))
    return out


@dataclass(frozen=True)
class Cpu:
    cpu: int
    package: int
    core: int
    node: int
    siblings: tuple


@dataclass(frozen=True)
class Card:
    address: str
    pci_class: str
    node: int              # -1: the firmware did not say
    local_cpus: tuple


@dataclass
class Topology:
    cpus: dict
    nodes: dict
    cards: dict
    net: dict = field(default_factory=dict)   # interface name -> PCI address

    def card_for(self, ifname):
        """The PCI device behind an interface; a card of unknown node (-1) when the interface is not a PCI device
        (a virtual machine's synthetic adapter)."""
        addr = self.net.get(ifname, "")
        return self.cards.get(addr, Card(addr, "", -1, tuple(sorted(self.cpus))))

    def physical_cores(self, node=None):
        seen = {}
        for c in sorted(self.cpus.values(), key=lambda x: x.cpu):
            if node is None or c.node == node:
                seen.setdefault((c.package, c.core), c.siblings)
        return list(seen.values())


def _read(p):
    return pathlib.Path(p).read_text().strip()


def read_topology(root="/"):
    root = pathlib.Path(root)
    nodes = {}
    for nd in sorted((root / "sys/devices/system/node").glob("node[0-9]*")):
        nodes[int(nd.name[4:])] = tuple(parse_cpulist(_read(nd / "cpulist")))
    node_of = {c: n for n, cs in nodes.items() for c in cs}
    cpus = {}
    for d in sorted((root / "sys/devices/system/cpu").glob("cpu[0-9]*")):
        t = d / "topology"
        if not t.exists():
            continue
        cpu = int(d.name[3:])
        cpus[cpu] = Cpu(cpu, int(_read(t / "physical_package_id")), int(_read(t / "core_id")), node_of.get(cpu, 0),
                        tuple(parse_cpulist(_read(t / "thread_siblings_list"))))
    cards = {}
    for d in sorted((root / "sys/bus/pci/devices").glob("*")):
        try:
            node = int(_read(d / "numa_node"))
            local = tuple(parse_cpulist(_read(d / "local_cpulist")))
        except (OSError, ValueError):
            continue
        cls = _read(d / "class") if (d / "class").exists() else ""
        cards[d.name] = Card(d.name, cls, node, local)
    net = {}
    for n in sorted((root / "sys/class/net").glob("*")):
        dev = n / "device"
        if dev.is_symlink():
            net[n.name] = pathlib.Path(dev.resolve()).name
        elif dev.is_file():
            net[n.name] = _read(dev)
    return Topology(cpus, nodes, cards, net)


@dataclass(frozen=True)
class Plan:
    node: int
    roles: dict            # role -> cpu
    idle: tuple            # siblings of hot cores, left idle
    housekeeping: tuple    # everything else: kernel, interrupts of other devices, cold threads


def plan(topo, ifname, hot=("feed", "strategy", "gateway"), cold=("logger",)):
    card = topo.card_for(ifname)
    node = card.node if card.node >= 0 else min(topo.nodes)
    cores = topo.physical_cores(node)
    # never give CPU 0's core to the hot path: the kernel and many drivers favour it
    cores = [s for s in cores if 0 not in s]
    if len(cores) < len(hot):
        raise ValueError(f"node {node} has {len(cores)} usable physical cores for {len(hot)} hot threads")
    roles, idle, used = {}, [], set()
    for role, sib in zip(hot, cores[-len(hot):], strict=True):   # take the highest-numbered cores
        roles[role] = sib[0]
        idle += list(sib[1:])
        used |= set(sib)
    house = tuple(c for c in sorted(topo.cpus) if c not in used)
    for role in cold:
        roles[role] = house[-1]
    return Plan(node, roles, tuple(sorted(idle)), house)


def check(p, topo, hot=("feed", "strategy", "gateway")):
    errs = []
    cores = {}
    for role in hot:
        c = topo.cpus[p.roles[role]]
        if c.node != p.node:
            errs.append(f"{role} on node {c.node}, card on node {p.node}")
        key = (c.package, c.core)
        if key in cores:
            errs.append(f"{role} shares a physical core with {cores[key]}")
        cores[key] = role
        for s in c.siblings:
            if s != c.cpu and s not in p.idle:
                errs.append(f"sibling {s} of {role}'s CPU {c.cpu} is not idle")
    if 0 not in p.housekeeping:
        errs.append("CPU 0 is not a housekeeping CPU")
    return errs


def remote_penalty_ns(lines_in, lines_out, local_ns, remote_ns):
    """Latency added per tick-to-trade when the lines a packet brings in and an order sends out each cross the socket
    interconnect once, one after the other, instead of moving within the socket."""
    return (lines_in + lines_out) * (remote_ns - local_ns)


def write_plan(p, path):
    lines = [f"# node {p.node}"] + [f"{role} {cpu}" for role, cpu in p.roles.items()]
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


def read_plan(path):
    out = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            role, cpu = line.split()
            out[role] = int(cpu)
    return out
