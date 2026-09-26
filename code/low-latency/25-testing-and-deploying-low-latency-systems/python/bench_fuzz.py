"""Chapter 25 measured data (not a fig_*.py, because sanitised binaries and their timings belong to the machine): the
fuzzer built with AddressSanitizer and UndefinedBehaviorSanitizer, run for a million mutated messages against the
firm's FIX parser, and against the parser that trusts BodyLength until the sanitiser stops it, for ten seeds. Output
measured_fuzz.csv (target, seed, iterations, accepted or first bad read, seconds)."""
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/low-latency/25-testing-and-deploying-low-latency-systems"
SRC = "code/low-latency/25-testing-and-deploying-low-latency-systems/cpp/ll_fuzz.cpp"
FLAGS = ("-std=c++20", "-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-Wall", "-Wextra",
         "-Werror")


def main():
    exe = u.compile_cpp(ROOT / SRC, flags=FLAGS, out=(ROOT / SRC).parent / "bin/ll_fuzz_asan")
    rows = []
    t0 = time.perf_counter()
    _, n, acc = u.run(exe, "real", 1_000_000, 1).strip().split(",")
    rows.append(["real", 1, n, acc, f"{time.perf_counter() - t0:.2f}"])
    for seed in range(1, 11):
        t0 = time.perf_counter()
        res = subprocess.run(["nice", "-n", str(u.NICE), str(exe), "trusting", str(seed)], cwd=ROOT,
                             capture_output=True, text=True, timeout=600)
        line = [x for x in res.stdout.splitlines() if x.startswith("trusting")][-1]
        _, s, it = line.split(",")
        found = "AddressSanitizer" in res.stderr
        rows.append(["trusting", s, it, "heap-buffer-overflow" if found else "none",
                     f"{time.perf_counter() - t0:.2f}"])
    u.write_measured(OUT / "measured_fuzz.csv", ["target", "seed", "iterations", "result", "seconds"], rows,
                     source=SRC, flags=" ".join(FLAGS))


if __name__ == "__main__":
    main()
