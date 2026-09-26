"""Chapter 15 measured data (not a fig_*.py): parsing and building FIX execution reports in C++ (zero-copy view,
std::map parser, fixed-buffer builder, string concatenation) and parsing them with the Python reference.
Output: measured_fix.csv (key, ns_per_msg)."""
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(ROOT / "code/firm/fixengine"))
import firm_fixengine as fx  # noqa: E402
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/15-protocols-i-fix"
SRC = "code/low-latency/15-protocols-i-fix/cpp/ll_fix_bench.cpp"


def python_decode_ns(n=1000, reps=21):
    msgs = []
    for i in range(n):
        q, done = 1 + i % 9, (1 + i % 9) // 2
        body = [(37, f"X{700000 + i}"), (11, f"ORD{i}"), (17, f"E{900000 + i}"), (150, "F"), (39, "1"), (55, "ESZ6"),
                (54, "1"), (38, q), (32, done), (31, f"5723.{10 + i % 80}"), (151, q - done), (14, done),
                (6, f"5723.{10 + i % 80}"), (60, "20260925-14:30:00.123456")]
        msgs.append(fx.encode(b"8", body, 1000 + i, "BROKER", "FIRM", 52_200_000 + i))
    best = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        for m in msgs:
            fx.decode(m)
        best.append((time.perf_counter_ns() - t0) / n)
    return sorted(best)[len(best) // 2]


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_fix_bench.cpp", includes=[ROOT / "code/firm/fixengine/cpp"])
    lines = u.run(exe, cpus=6).strip().splitlines()
    rows = [x.split(",") for x in lines[1:]]
    mean_bytes = next(r[1] for r in rows if r[0] == "bytes")
    rows = [r for r in rows if r[0] != "bytes"]
    rows.insert(2, ["python", f"{python_decode_ns():.1f}"])     # order: view, map, python, builder, concat
    u.write_measured(OUT / "measured_fix.csv", ["key", "ns_per_msg"], rows, cpus="6", source=SRC,
                     mean_bytes=mean_bytes,
                     python="firm_fixengine.decode, CPython " + sys.version.split()[0] + ", median of 21 passes")


if __name__ == "__main__":
    main()
