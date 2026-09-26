"""firm.flagbench -- choose compiler flags by measurement (build of One Quant Book 13, chapter 8).

A benchmark is a C++ program whose first output line is a result checksum and whose second is a time (ns per unit of
work). `run_matrix` builds it under each flag set (profile-guided sets are built twice: instrumented, trained, rebuilt),
runs each binary, checks that every checksum equals the reference set's, and returns the rows ranked by time. A flag set
that changes the checksum is reported, never ranked: faster and wrong is wrong.

API (stable):
    FlagSet(name, flags, pgo=False)
    build(sources, fs, out_dir, train_args=(), includes=()) -> Path
    run_matrix(sources, flag_sets, args=(), reference=0, repeats=3, cpus=None, includes=()) -> list[dict]
        dict: name, flags, checksum, ns, ok (checksum equals the reference), speedup (reference ns / ns)
"""
import pathlib
import shutil
import subprocess
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ubench"))
import firm_ubench as u  # noqa: E402

BASE = ("-std=c++20", "-Wall", "-Wextra")


@dataclass(frozen=True)
class FlagSet:
    name: str
    flags: tuple
    pgo: bool = False


def _compile(sources, flags, out, includes):
    cmd = ["g++", *BASE, *flags, *[f"-I{i}" for i in includes], *map(str, sources), "-o", str(out)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def build(sources, fs, out_dir, train_args=(), includes=()):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = out_dir / fs.name.replace(" ", "_").replace("+", "p").replace("/", "_")
    if not fs.pgo:
        _compile(sources, fs.flags, exe, includes)
        return exe
    prof = out_dir / (exe.name + ".prof")
    shutil.rmtree(prof, ignore_errors=True)
    _compile(sources, (*fs.flags, f"-fprofile-generate={prof}"), exe, includes)
    subprocess.run([str(exe), *map(str, train_args)], check=True, capture_output=True, cwd=u.ROOT)
    use = (f"-fprofile-use={prof}", "-fprofile-correction", "-Wno-missing-profile")
    _compile(sources, (*fs.flags, *use), exe, includes)
    return exe


def run_matrix(sources, flag_sets, args=(), reference=0, repeats=3, cpus=None, includes=(), out_dir=None):
    out_dir = pathlib.Path(out_dir or pathlib.Path(sources[0]).parent / "bin" / "flagbench")
    rows = []
    for fs in flag_sets:
        exe = build(sources, fs, out_dir, train_args=args, includes=includes)
        best, checksum = float("inf"), None
        for _ in range(repeats):
            lines = u.run(exe, *args, cpus=cpus).strip().splitlines()
            checksum, ns = lines[0].strip(), float(lines[1])
            best = min(best, ns)
        rows.append({"name": fs.name, "flags": " ".join(fs.flags) + (" +PGO" if fs.pgo else ""), "checksum": checksum,
                     "ns": best})
    ref = rows[reference]
    for r in rows:
        r["ok"] = r["checksum"] == ref["checksum"]
        r["speedup"] = ref["ns"] / r["ns"]
    return rows
