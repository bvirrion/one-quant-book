"""Chapter 9 measured data (not a fig_*.py): the Rust crate's benchmark (cargo build --release) and its C++ twin.
Output: measured_decode.csv (ns per message) and measured_loops.csv (ns per element), columns task, cpp, rust."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/09-rust-for-low-latency/measured_twins.csv"


def _table(text):
    return dict(line.split(",") for line in text.strip().splitlines()[1:])


def main():
    subprocess.run(["cargo", "build", "--release", "-j", "2", "--bin", "ll_rust_bench"], cwd=HERE / "rust", check=True,
                   capture_output=True)
    rust = _table(u.run(HERE / "rust/target/release/ll_rust_bench", cpus="2"))
    cpp = _table(u.run(u.compile_cpp(HERE / "cpp/ll_twin_bench.cpp"), cpus="2"))
    meta = dict(flags=" ".join(u.DEFAULT) + "; cargo --release (opt-level 3)", cpus="2",
                source="code/low-latency/09-rust-for-low-latency/{cpp/ll_twin_bench.cpp,rust/src/bin/ll_rust_bench.rs}")
    for name, tasks in (("decode", ("decode",)), ("loops", ("counted loop", "gather checked", "gather unchecked"))):
        rows = [[t, cpp[f"C++ {t}"], rust[f"rust {t}"]] for t in tasks]
        u.write_measured(OUT.with_name(f"measured_{name}.csv"), ["task", "cpp", "rust"], rows, **meta)


if __name__ == "__main__":
    main()
