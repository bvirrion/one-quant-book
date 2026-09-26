"""Write synthetic sysfs trees for firm.coreplan's tests (not copies of real machines).

two_socket: 2 packages x 8 cores x 2 threads (CPUs 0-15 on socket 0, 16-31 on socket 1; sibling of CPU c is c + 8 within
each socket), NUMA nodes 0 and 1, a network card at 0000:81:00.0 on node 1 named ens1f0, a disk controller on node 0.
one_node: 1 package x 4 cores x 2 threads, one node, a card that reports numa_node -1 (unknown), as laptops and many
virtual machines do.
"""
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent


def cpulist(cpus):
    cpus = sorted(cpus)
    out, start = [], cpus[0]
    for a, b in zip(cpus, cpus[1:] + [None], strict=True):
        if b != a + 1:
            out.append(f"{start}-{a}" if a != start else f"{a}")
            start = b
    return ",".join(out)


def write(root, packages, cores, threads, cards):
    root = HERE / "data" / root
    shutil.rmtree(root, ignore_errors=True)
    per_pkg = cores * threads
    for p in range(packages):
        node_cpus = []
        for c in range(cores):
            sib = [p * per_pkg + c + t * cores for t in range(threads)]
            for cpu in sib:
                d = root / f"sys/devices/system/cpu/cpu{cpu}/topology"
                d.mkdir(parents=True, exist_ok=True)
                (d / "core_id").write_text(f"{c}\n")
                (d / "physical_package_id").write_text(f"{p}\n")
                (d / "thread_siblings_list").write_text(cpulist(sib) + "\n")
            node_cpus += sib
        nd = root / f"sys/devices/system/node/node{p}"
        nd.mkdir(parents=True, exist_ok=True)
        (nd / "cpulist").write_text(cpulist(node_cpus) + "\n")
    for addr, cls, node, ifname in cards:
        d = root / f"sys/bus/pci/devices/{addr}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "class").write_text(cls + "\n")
        (d / "numa_node").write_text(f"{node}\n")
        local = [c for c in range(packages * per_pkg) if node < 0 or c // per_pkg == node]
        (d / "local_cpulist").write_text(cpulist(local) + "\n")
        if ifname:
            n = root / f"sys/class/net/{ifname}"
            n.mkdir(parents=True, exist_ok=True)
            (n / "device").write_text(addr + "\n")  # a real tree has a symlink; the fixture stores its target


def main():
    write("two_socket", 2, 8, 2, [("0000:81:00.0", "0x020000", 1, "ens1f0"), ("0000:03:00.0", "0x010802", 0, None)])
    write("one_node", 1, 4, 2, [("0000:00:1f.6", "0x020000", -1, "eth0")])


if __name__ == "__main__":
    main()
