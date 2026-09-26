"""Chapter 4 of One Quant Book 13: reading the measured core-to-core matrix, and the arithmetic of remote placement."""
import csv
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/coreplan"))
import firm_coreplan as cp  # noqa: E402

FIG = ROOT / "figdata/low-latency/04-multi-socket-machines-and-interconnects"


def c2c():
    with open(FIG / "measured_c2c.csv", newline="") as f:
        return {(int(r["a"]), int(r["b"])): float(r["ns"]) for r in csv.DictReader(f)}


def classes(threshold=100.0):
    """Split off-diagonal pairs into fast and slow by a threshold; return (fast pairs, fast median, slow median)."""
    m = c2c()
    off = {k: v for k, v in m.items() if k[0] < k[1]}
    fast = sorted(k for k, v in off.items() if v < threshold)
    return fast, statistics.median(off[k] for k in fast), statistics.median(v for k, v in off.items() if v >= threshold)


def pcie_gbytes(gt_per_s, lanes, enc=(128, 130)):
    """Usable bytes per second and direction of a PCIe link, in GB/s."""
    return gt_per_s * lanes * enc[0] / enc[1] / 8


def remote_penalty(lines_in=2, lines_out=2, local=59.0, remote=138.0):
    return cp.remote_penalty_ns(lines_in, lines_out, local, remote)
