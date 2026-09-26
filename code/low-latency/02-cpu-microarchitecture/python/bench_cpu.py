"""Chapter 2 measured data (not a fig_*.py; `make figdata` never runs it).

measured_branch.csv   ns per element of the 2012 loop: order, branchy, branchless (CPU 2)
measured_chains.csv   ns per addition with 1..16 independent accumulators (CPU 2)
measured_blocks.csv   ns per element of the branchy loop when values alternate in blocks of b (exercise 7)
measured_freq.csv     per virtual CPU: clock from a register add chain, adds per cycle of an add-immediate chain
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/02-cpu-microarchitecture"
SRC = "code/low-latency/02-cpu-microarchitecture/cpp/ll_cpu_bench.cpp"


def _table(text):
    lines = text.strip().splitlines()
    return lines[0].split(","), [line.split(",") for line in lines[1:]]


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_cpu_bench.cpp")
    flags = " ".join(u.DEFAULT)
    _, rows = _table(u.run(exe, "branch", cpus="2"))
    ns = {(v, o): x for v, o, x in rows}
    u.write_measured(OUT / "measured_branch.csv", ["order", "branchy", "branchless"],
                     [[o, ns[("branchy", o)], ns[("branchless", o)]] for o in ("sorted", "shuffled")],
                     flags=flags, cpus="2", unit="ns per element", source=SRC)
    for mode in ("chains", "blocks"):
        h, rows = _table(u.run(exe, mode, cpus="2"))
        u.write_measured(OUT / f"measured_{mode}.csv", h, rows, flags=flags, cpus="2", source=SRC)
    rows = []
    for cpu in range(os.cpu_count()):
        h, r = _table(u.run(exe, "freq", cpus=str(cpu)))
        rows.append([cpu, *r[0]])
    u.write_measured(OUT / "measured_freq.csv", ["cpu", *h], rows, flags=flags, cpus="each in turn", source=SRC)


if __name__ == "__main__":
    main()
