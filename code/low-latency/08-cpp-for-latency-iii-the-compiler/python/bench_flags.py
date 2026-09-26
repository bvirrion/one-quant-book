"""Chapter 8 measured data (not a fig_*.py): the decode benchmark under a matrix of flag sets with firm.flagbench.
Output: measured_flags.csv (name, flags, ns, speedup over -O2, ok) and measured_fastmath.csv (a float sum)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/flagbench"))
import firm_flagbench as fb  # noqa: E402

u = fb.u
HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/08-cpp-for-latency-iii-the-compiler/measured_flags.csv"
SOURCES = [HERE / "cpp/ll_flags_main.cpp", HERE / "cpp/ll_handle.cpp"]
SETS = [
    fb.FlagSet("O2", ("-O2",)),
    fb.FlagSet("O0", ("-O0",)),
    fb.FlagSet("O3", ("-O3",)),
    fb.FlagSet("O2 native", ("-O2", "-march=native")),
    fb.FlagSet("O2 LTO", ("-O2", "-flto")),
    fb.FlagSet("O2 PGO", ("-O2",), pgo=True),
    fb.FlagSet("O3 native LTO PGO", ("-O3", "-march=native", "-flto"), pgo=True),
]


FP_SETS = [fb.FlagSet("O2", ("-O2",)), fb.FlagSet("O3 native", ("-O3", "-march=native")),
           fb.FlagSet("O3 native fast-math", ("-O3", "-march=native", "-ffast-math"))]
FP_OUT = OUT.with_name("measured_fastmath.csv")


def main():
    fp = fb.run_matrix([HERE / "cpp/ll_fpsum.cpp"], FP_SETS, repeats=5, cpus="2")
    u.write_measured(FP_OUT, ["name", "checksum", "ns", "speedup", "ok"],
                     [[r["name"], r["checksum"], f"{r['ns']:.4f}", f"{r['speedup']:.3f}", int(r["ok"])] for r in fp],
                     cpus="2", source="code/low-latency/08-cpp-for-latency-iii-the-compiler/cpp/ll_fpsum.cpp")
    rows = fb.run_matrix(SOURCES, SETS, args=(300,), repeats=5, cpus="2")
    u.write_measured(OUT, ["name", "flags", "ns", "speedup", "ok"],
                     [[r["name"], r["flags"], f"{r['ns']:.3f}", f"{r['speedup']:.3f}", int(r["ok"])] for r in rows],
                     cpus="2", compiler_driver="firm_flagbench.run_matrix, best of 5",
                     source="code/low-latency/08-cpp-for-latency-iii-the-compiler/cpp/ll_flags_main.cpp")


if __name__ == "__main__":
    main()
