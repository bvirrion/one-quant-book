"""Chapter 13 measured data (not a fig_*.py): what this untuned machine does to a spinning thread (the hiccup meter
alone and pinned, unpinned, and sharing its CPU with a rival spinner), receive latencies (loopback UDP blocking and
busy-polled, a pipe ping-pong on one CPU and on two), page faults with and without mlockall, the privileges an
ordinary process lacks, and firm.tuneaudit's verdict on the machine.
Outputs measured_hiccups.csv, measured_hiccup_summary.csv, measured_receive.csv, measured_mlock.csv,
measured_privileges.csv and measured_audit.csv."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(ROOT / "code/firm/coreplan"))
sys.path.insert(0, str(ROOT / "code/firm/tuneaudit"))
import firm_coreplan as cp  # noqa: E402
import firm_tuneaudit as ta  # noqa: E402
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/13-linux-tuning"
SRC = "code/low-latency/13-linux-tuning/cpp/ll_tuning_bench.cpp"
SECONDS = 5


def hiccups(exe, compete, cpus):
    rows = [x.split(",") for x in u.run(exe, "hiccup", SECONDS, compete, cpus=cpus).strip().splitlines()]
    s = next(r for r in rows if r[0] == "summary")
    elapsed = float(s[1])
    exc = {int(r[1]): int(r[2]) / (elapsed / 1e9) for r in rows if r[0] == "exc"}
    wait = {int(r[1]): float(r[2]) for r in rows if r[0] == "wait"}
    mean = next(float(r[1]) for r in rows if r[0] == "meanwait")
    summary = [elapsed / 1e9, int(s[5]), int(s[2]), float(s[3]) / elapsed, float(s[4]), mean, wait[10000],
               wait[100000]]
    return exc, summary


def kernel_config():
    """CONFIG_HZ and CONFIG_NO_HZ_FULL of the running kernel, when it exposes its configuration."""
    import gzip
    try:
        text = gzip.open("/proc/config.gz", "rt").read()
    except OSError:
        return dict(config_hz="unknown", no_hz_full="unknown")
    hz = next((x.split("=")[1] for x in text.splitlines() if x.startswith("CONFIG_HZ=")), "unknown")
    return dict(config_hz=hz, no_hz_full="y" if "CONFIG_NO_HZ_FULL=y" in text else "not set")


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_tuning_bench.cpp")
    runs = {"alone": ("0", 6), "unpinned": ("0", None), "shared": ("1", 6)}
    curves, summ = {}, []
    for key, (compete, cpus) in runs.items():
        curves[key], s = hiccups(exe, compete, cpus)
        summ.append([key, *(f"{x:.6g}" for x in s)])
    grid = sorted(curves["alone"])
    rows = [[g, *(f"{curves[k][g]:.4g}" for k in runs)] for g in grid]
    meta = dict(cpus="hiccup: CPU 6 (alone, shared) or any (unpinned); receive: CPUs 6 and 7", seconds=SECONDS,
                source=SRC, **kernel_config())
    u.write_measured(OUT / "measured_hiccups.csv", ["threshold_ns", *runs], rows, **meta)
    u.write_measured(OUT / "measured_hiccup_summary.csv",
                     ["scenario", "seconds", "loops", "gaps", "stolen_fraction", "worst_ns", "mean_wait_ns",
                      "p_wait_10us", "p_wait_100us"], summ, **meta)

    rec = []
    for args in [("udp", 100000, "block", 6, 7), ("udp", 100000, "spin", 6, 7), ("ctx", 100000, 6, 6),
                 ("ctx", 100000, 6, 7)]:
        rec.append(u.run(exe, *args).strip().split(","))   # key: udp-block, udp-spin, pipe-same, pipe-two
    u.write_measured(OUT / "measured_receive.csv", ["key", "p50", "p99", "p999", "max"], rec, **meta)

    lines = [x.split(",") for x in u.run(exe, "mlock", 32).strip().splitlines()]
    err = next(r[1] for r in lines if r[0] == "errno")
    u.write_measured(OUT / "measured_mlock.csv", ["case", "faults", "map_ns_per_page", "touch_ns_per_page"],
                     [r for r in lines if r[0] != "errno"], mib=32, mlockall_errno=err, source=SRC)
    priv = [x.split(",") for x in u.run(exe, "privileges").strip().splitlines()]
    u.write_measured(OUT / "measured_privileges.csv", ["request", "result"], priv, source=SRC)

    topo = cp.read_topology("/")
    findings = ta.audit("/", cp.plan(topo, "eth0"))
    u.write_measured(OUT / "measured_audit.csv", ["rule", "status", "detail"],
                     [[f.rule, f.status, f.detail.replace(",", ";")] for f in findings],
                     source="code/firm/tuneaudit/firm_tuneaudit.py", plan="firm.coreplan on this machine, eth0",
                     **kernel_config())


if __name__ == "__main__":
    main()
