"""firm.ubench -- Python side of the microbenchmark harness (build of One Quant Book 13, chapter 2).

Book 13's measured charts are produced by `bench_*.py` drivers (never `fig_*.py`, so `make figdata` does not rerun
them). A driver compiles a C++ (or Rust) benchmark, runs it, and writes `measured_*.csv` with a `.meta` sidecar that
records where and how the numbers were taken: machine, date, compiler and flags, CPU list, load average.

API (stable):
    ROOT                                   repository root
    compile_cpp(src, flags=DEFAULT, includes=()) -> Path   builds into <src dir>/bin/, rebuilt when a source is newer
    run(exe, *args, cpus=None, timeout=900) -> str         stdout; `cpus` pins with taskset (e.g. "2" or "2,4");
                                                           runs under `nice -n $OQB_BENCH_NICE` (default 19; 0: none)
    $OQB_BENCH_SHARED                                      the .meta "shared" line (default: other jobs may have run)
    machine() -> dict                                      cpu model, logical cpus, kernel, g++/rustc versions, load
    write_measured(csv_path, header, rows, **meta)         CSV + `<csv>.meta` (key: value lines)
    read_csv(path) -> list[dict]                           rows of a measured or deterministic CSV (strings)
    quantiles(x, ps) -> list[float]                        nearest-rank quantiles, same rule as firm::ubench::quantile
"""
import csv
import datetime as dt
import math
import os
import pathlib
import platform
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT = ("-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror")
UBENCH_INC = ROOT / "code/firm/ubench/cpp"


def compile_cpp(src, flags=DEFAULT, includes=(), out=None):
    src = pathlib.Path(src)
    out = pathlib.Path(out) if out else src.parent / "bin" / src.stem
    out.parent.mkdir(parents=True, exist_ok=True)
    incs = [src.parent, UBENCH_INC, *map(pathlib.Path, includes)]
    deps = [src, *[h for d in incs for h in d.glob("*.hpp")]]
    if not out.exists() or any(d.stat().st_mtime > out.stat().st_mtime for d in deps):
        cmd = ["g++", *flags, *[f"-I{d}" for d in incs], str(src), "-o", str(out)]
        subprocess.run(cmd, check=True, cwd=ROOT)
    return out


NICE = int(os.environ.get("OQB_BENCH_NICE", "19"))   # benchmarks yield to other work unless told otherwise


def run(exe, *args, cpus=None, timeout=900):
    cmd = [str(exe), *map(str, args)]
    if cpus is not None and shutil.which("taskset"):
        cmd = ["taskset", "-c", str(cpus), *cmd]
    if NICE and shutil.which("nice"):
        cmd = ["nice", "-n", str(NICE), *cmd]
    return subprocess.run(cmd, check=True, cwd=ROOT, capture_output=True, text=True, timeout=timeout).stdout


def _first_line(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.splitlines()[0]
    except (OSError, IndexError):
        return "unavailable"


def machine():
    model = "unknown"
    try:
        for line in open("/proc/cpuinfo", encoding="utf8"):
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    load = os.getloadavg()
    return {
        "cpu": model,
        "logical_cpus": os.cpu_count(),
        "kernel": platform.release(),
        "gxx": _first_line(["g++", "--version"]),
        "rustc": _first_line(["rustc", "--version"]),
        "loadavg_1_5_15": " ".join(f"{x:.2f}" for x in load),
        "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def write_measured(csv_path, header, rows, **meta):
    csv_path = pathlib.Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    info = {**machine(), **meta}
    info.setdefault("nice", NICE)
    info.setdefault("isolated_cores", "none")
    info.setdefault("shared", os.environ.get("OQB_BENCH_SHARED", "yes: other jobs may have run on the machine"))
    with open(str(csv_path) + ".meta", "w", encoding="utf8") as f:
        for k, v in info.items():
            f.write(f"{k}: {v}\n")


def read_csv(path):
    with open(path, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def quantiles(x, ps):
    v = sorted(x)
    n = len(v)
    return [v[min(n - 1, math.floor(p * n))] for p in ps]
