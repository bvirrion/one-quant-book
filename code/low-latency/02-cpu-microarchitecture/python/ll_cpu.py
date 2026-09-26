"""Chapter 2 of One Quant Book 13: what the measured kernels imply (misprediction penalty, break-even rate,
chains needed to saturate the adders). Reads the committed measured CSVs; nothing here times anything."""
import csv
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[4]
FIG = ROOT / "figdata/low-latency/02-cpu-microarchitecture"


def _rows(name):
    with open(FIG / name, newline="") as f:
        return list(csv.DictReader(f))


def branch():
    r = {}
    for x in _rows("measured_branch.csv"):
        for v in ("branchy", "branchless"):
            r[(v, x["order"])] = float(x[v])
    return r


def clock_ghz(cpu=2):
    return [float(x["ghz_reg"]) for x in _rows("measured_freq.csv") if int(x["cpu"]) == cpu][0]


def penalty(miss_rate=0.5, cpu=2):
    """Misprediction penalty in ns and in cycles: the shuffled-minus-sorted cost per element over the miss rate."""
    b = branch()
    ns = (b[("branchy", "shuffled")] - b[("branchy", "sorted")]) / miss_rate
    return ns, ns * clock_ghz(cpu)


def break_even(miss_rate=0.5, cpu=2):
    """Misprediction rate above which the branchless loop wins: its extra cost per element over the penalty."""
    b = branch()
    extra = b[("branchless", "sorted")] - b[("branchy", "sorted")]
    return extra / penalty(miss_rate, cpu)[0]


def chains():
    return {int(x["accumulators"]): float(x["ns_per_add"]) for x in _rows("measured_chains.csv")}


def freq_summary():
    g = [float(x["ghz_reg"]) for x in _rows("measured_freq.csv")]
    k = [float(x["adds_per_cycle_imm"]) for x in _rows("measured_freq.csv")]
    return min(g), max(g), statistics.median(g), statistics.median(k)


def chains_needed(latency_cycles, per_cycle):
    """Little's law for the adders: independent chains needed to keep every adder busy."""
    return latency_cycles * per_cycle


def branch_cost(base, miss_rate, penalty_cycles):
    return base + miss_rate * penalty_cycles
