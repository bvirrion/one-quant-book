"""firm.tuneaudit -- audit a Linux host against a core placement plan (build of One Quant Book 13, chapter 13).

firm.coreplan decides which CPUs run the hot threads and which siblings stay idle; this module checks that the host
was tuned for that plan, from the files the kernel exposes under /proc and /sys (or a fixture tree with the same
layout), and reports every deviation. It changes nothing: tuning is done by the host's configuration management, the
audit is what a deployment runs before it starts the trading process (chapter 25).

API (stable):
    audit(root, plan, hot=("feed", "strategy", "gateway"), memlock_bytes=1 << 30, fifo=False) -> list[Finding]
    Finding(rule, status, detail)       status: "ok", "fail" or "unknown" (the host does not expose the setting)
    failures(findings) -> list[Finding]
    report(findings) -> str            one line per rule
    RULES                               the rule names, in the order audit() reports them
"""
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "coreplan"))
from firm_coreplan import parse_cpulist  # noqa: E402

RULES = ("isolated", "siblings", "nohz_full", "rcu_nocbs", "irq_affinity", "irqbalance", "governor", "cstate",
         "thp", "memlock", "rt_throttle")


@dataclass(frozen=True)
class Finding:
    rule: str
    status: str
    detail: str


def _text(root, rel):
    p = pathlib.Path(root) / rel
    return p.read_text().strip() if p.is_file() else None


def cmdline_params(text):
    """Boot parameters as {name: value}; a flag without '=' maps to ''."""
    out = {}
    for tok in (text or "").split():
        k, _, v = tok.partition("=")
        out[k] = v
    return out


def mask_cpus(hexmask):
    """CPUs of a hexadecimal mask as /proc/irq/default_smp_affinity prints it (32-bit groups separated by commas)."""
    v = int(hexmask.replace(",", ""), 16)
    return {i for i in range(v.bit_length()) if v >> i & 1}


def selected(text):
    """The bracketed choice of a sysfs selector such as 'always [madvise] never'."""
    return text[text.index("[") + 1:text.index("]")] if text and "[" in text else text


def _fmt(cpus):
    return ",".join(str(c) for c in sorted(cpus)) or "none"


def audit(root, plan, hot=("feed", "strategy", "gateway"), memlock_bytes=1 << 30, fifo=False):
    root = pathlib.Path(root)
    hot_cpus = {plan.roles[r] for r in hot}
    idle = set(plan.idle)
    cmd = cmdline_params(_text(root, "proc/cmdline"))
    out = []

    def add(rule, ok, detail, unknown=False):
        out.append(Finding(rule, "unknown" if unknown else ("ok" if ok else "fail"), detail))

    isolated = set(parse_cpulist(_text(root, "sys/devices/system/cpu/isolated") or ""))
    miss = hot_cpus - isolated
    add("isolated", not miss, f"hot CPUs not isolated: {_fmt(miss)}" if miss else f"isolated {_fmt(isolated)}")

    online = {c for c in idle if _text(root, f"sys/devices/system/cpu/cpu{c}/online") != "0"}
    busy = online - isolated
    add("siblings", not busy, f"idle siblings online and not isolated: {_fmt(busy)}" if busy else "siblings idle")

    nohz = _text(root, "sys/devices/system/cpu/nohz_full")
    if nohz is None:
        add("nohz_full", False, "kernel built without adaptive ticks (no nohz_full file)")
    else:
        miss = hot_cpus - set(parse_cpulist(nohz))
        add("nohz_full", not miss, f"ticking hot CPUs: {_fmt(miss)}" if miss else f"nohz_full {nohz}")

    offloaded = set(parse_cpulist(cmd.get("rcu_nocbs", ""))) | set(parse_cpulist(nohz or ""))
    miss = hot_cpus - offloaded
    add("rcu_nocbs", not miss, f"RCU callbacks run on {_fmt(miss)}" if miss else "RCU callbacks offloaded")

    bad = []
    dflt = _text(root, "proc/irq/default_smp_affinity")
    if dflt is not None and mask_cpus(dflt) & hot_cpus:
        bad.append("default")
    for d in sorted((root / "proc/irq").glob("[0-9]*"), key=lambda p: int(p.name)):
        cpus = _text(root, f"proc/irq/{d.name}/smp_affinity_list")
        if cpus is not None and set(parse_cpulist(cpus)) & hot_cpus:
            bad.append(d.name)
    shown = ", ".join(bad[:5]) + (f" and {len(bad) - 5} more" if len(bad) > 5 else "")
    add("irq_affinity", not bad, f"interrupts allowed on hot CPUs: {shown}" if bad else "no interrupt on hot CPUs")

    procs = [p for p in root.glob("proc/[0-9]*") if _text(root, f"proc/{p.name}/comm") == "irqbalance"]
    add("irqbalance", not procs, f"irqbalance running (pid {procs[0].name})" if procs else "irqbalance not running")

    govs = {c: _text(root, f"sys/devices/system/cpu/cpu{c}/cpufreq/scaling_governor") for c in sorted(hot_cpus)}
    if all(g is None for g in govs.values()):
        add("governor", False, "no frequency governor exposed (virtual machine?)", unknown=True)
    else:
        slow = {c: g for c, g in govs.items() if g != "performance"}
        add("governor", not slow, ", ".join(f"CPU {c}: {g}" for c, g in slow.items()) if slow else "performance")

    deep = cmd.get("intel_idle.max_cstate"), cmd.get("processor.max_cstate")
    capped = cmd.get("idle") == "poll" or any(v is not None and v.isdigit() and int(v) <= 1 for v in deep)
    add("cstate", capped, "idle states capped" if capped else "deep idle states allowed (no max_cstate or idle=poll)")

    en = selected(_text(root, "sys/kernel/mm/transparent_hugepage/enabled"))
    df = selected(_text(root, "sys/kernel/mm/transparent_hugepage/defrag"))
    if en is None:
        add("thp", False, "no transparent huge page controls", unknown=True)
    else:
        ok = en in ("madvise", "never") and df != "always"
        add("thp", ok, f"enabled={en}, defrag={df}")

    lim = _text(root, "proc/self/limits")
    line = next((x for x in (lim or "").splitlines() if x.startswith("Max locked memory")), None)
    if line is None:
        add("memlock", False, "no limits file", unknown=True)
    else:
        soft = line.split()[3]
        ok = soft == "unlimited" or int(soft) >= memlock_bytes
        add("memlock", ok, f"locked-memory limit {soft} bytes, need {memlock_bytes}")

    rt = _text(root, "proc/sys/kernel/sched_rt_runtime_us")
    if not fifo:
        add("rt_throttle", True, "hot threads not real-time: throttling irrelevant")
    else:
        add("rt_throttle", rt == "-1", f"sched_rt_runtime_us={rt}")
    return out


def failures(findings):
    return [f for f in findings if f.status == "fail"]


def report(findings):
    return "\n".join(f"{f.status:8s}{f.rule:14s}{f.detail}" for f in findings)


def main(argv=None):
    import firm_coreplan as cp
    argv = sys.argv[1:] if argv is None else argv
    root = argv[0] if argv else "/"
    ifname = argv[1] if len(argv) > 1 else "eth0"
    topo = cp.read_topology(root)
    findings = audit(root, cp.plan(topo, ifname))
    print(report(findings))
    return 1 if failures(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
