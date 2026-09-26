"""Chapter 25 figure data (deterministic, from the committed measured pools of bench_gate.py): the gate's false-alarm
rate (two disjoint draws from the A runs), its detection rate for a 5% rise in the 99th percentile (one draw shifted
by 5% of the median), and for the planted regression (A against B), against the number of runs per side. Outputs
gate.csv and gate_summary.csv (medians, spread, measured rise, runs needed by the normal approximation), and
gate_runs_plot.csv (the runs with a numeric variant column for the scatter plot)."""
import csv
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/perfgate"))
import firm_perfgate as pg  # noqa: E402

FIG = ROOT / "figdata/low-latency/25-testing-and-deploying-low-latency-systems"
NS = (5, 10, 20, 40, 80, 120, 160, 200)
TRIALS = 100


def pools():
    with open(FIG / "measured_gate_runs.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    a = [float(r["p99_ns"]) for r in rows if r["variant"] == "A"]
    b = [float(r["p99_ns"]) for r in rows if r["variant"] == "B"]
    return a, b


def robust_cv(x):
    med = statistics.median(x)
    mad = statistics.median(abs(v - med) for v in x)
    return 1.4826 * mad / med


def main():
    a, b = pools()
    with open(FIG / "measured_gate_runs.csv", newline="") as f, open(FIG / "gate_runs_plot.csv", "w", newline="") as g:
        w = csv.writer(g)
        w.writerow(["run", "isb", "p99_ns"])
        w.writerows([r["run"], int(r["variant"] == "B"), r["p99_ns"]] for r in csv.DictReader(f))
    med = statistics.median(a)
    shift = 0.05 * med
    with open(FIG / "gate.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["runs", "false_alarm", "detect_5pct", "detect_planted"])
        for n in NS:
            w.writerow([n, f"{pg.power(a, a, n, TRIALS):.3f}", f"{pg.power(a, a, n, TRIALS, shift=shift):.3f}",
                        f"{pg.power(a, b, n, TRIALS):.3f}"])
    cv = robust_cv(a)
    with open(FIG / "gate_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "value"])
        w.writerows([["median_p99_a_ns", f"{med:.1f}"], ["median_p99_b_ns", f"{statistics.median(b):.1f}"],
                     ["planted_rise", f"{statistics.median(b) / med - 1:.4f}"], ["robust_cv", f"{cv:.4f}"],
                     ["runs_needed_5pct_90pct", f"{pg.runs_needed(cv, 0.05):.0f}"]])


if __name__ == "__main__":
    main()
