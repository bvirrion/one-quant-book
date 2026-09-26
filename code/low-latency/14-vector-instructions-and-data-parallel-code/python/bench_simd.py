"""Chapter 14 measured data (not a fig_*.py): the delimiter scan by message length (scalar, SSE2, AVX2), the split of
FIX-like messages, eight-digit and price parsing, and the revaluation of an options book stored as records or as
columns at three flag sets. Outputs measured_scan.csv, measured_split.csv, measured_parse.csv, measured_reval.csv."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/14-vector-instructions-and-data-parallel-code"
SRC = "code/low-latency/14-vector-instructions-and-data-parallel-code/cpp/ll_simd_bench.cpp"
INC = [ROOT / "code/firm/simdscan/cpp"]
CPU = 6
REVAL = {"O2": ("-O2",), "O3": ("-O3",), "O3avx2": ("-O3", "-mavx2", "-mfma")}


def table(text):
    lines = text.strip().splitlines()
    return lines[0].split(","), [x.split(",") for x in lines[1:]]


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_simd_bench.cpp", includes=INC)
    meta = dict(cpus=str(CPU), source=SRC, flags="-std=c++20 -O2 (scan, split, parse: explicit intrinsics)")
    for mode in ("scan", "split"):
        head, rows = table(u.run(exe, mode, cpus=CPU))
        u.write_measured(OUT / f"measured_{mode}.csv", head, rows, **meta)
    head, rows = table(u.run(exe, "parse", cpus=CPU))
    keys = {"scalar loop": "scalar", "SWAR": "swar", "SSE4.1": "sse", "from_chars": "fromchars",
            "parse_fixed": "fixed", "strtod": "strtod"}
    u.write_measured(OUT / "measured_parse.csv", ["key", "ns"], [[keys[r[0]], r[1]] for r in rows], **meta)
    out = []
    for key, flags in REVAL.items():
        e = u.compile_cpp(HERE / "cpp/ll_simd_bench.cpp", flags=("-std=c++20", *flags, "-Wall", "-Wextra", "-Werror"),
                          includes=INC, out=HERE / "cpp/bin" / f"ll_simd_bench_{key}")
        _, rows = table(u.run(e, "reval", cpus=CPU))
        small, big = rows
        out.append([key, small[1], small[2], big[1], big[2]])
    u.write_measured(OUT / "measured_reval.csv", ["key", "rows_1k", "cols_1k", "rows_1m", "cols_1m"], out,
                     cpus=str(CPU), source=SRC, flags="key: O2 = -O2, O3 = -O3, O3avx2 = -O3 -mavx2 -mfma",
                     options="1,024 (in cache) and 1,048,576 (80 MB of records, 40 MB of columns)")


if __name__ == "__main__":
    main()
