"""Chapter 16 measured data (not a fig_*.py): decode cost per message of 60 seconds of the simulator's line A
(Book 1's decoder, generated big-endian flyweights, SBE-style little-endian flyweights, whole packets in C++ and in
Rust) and the arbitration cost per packet. The lines are regenerated (deterministic) in a temporary directory, and
the C++ arbiter's counts are checked against the Python reference. Outputs measured_decode.csv, measured_arb.csv."""
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_lines as L  # noqa: E402

ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/low-latency/16-protocols-ii-binary-exchange-protocols"
SRC = "code/low-latency/16-protocols-ii-binary-exchange-protocols/cpp/ll_wire_bench.cpp"


def main():
    exe = u.compile_cpp(HERE.parent / "cpp/ll_wire_bench.cpp",
                        includes=[ROOT / "code/firm/wirecodec/cpp", ROOT / "code/firm/feed/cpp"])
    crate = HERE.parent / "rust"
    subprocess.run(["nice", "-n", str(u.NICE), "cargo", "build", "-q", "--release"], cwd=crate, check=True)
    with tempfile.TemporaryDirectory() as d:
        L.record(60, d)
        a, b = pathlib.Path(d) / "lineA.bin", pathlib.Path(d) / "lineB.bin"
        rows = [x.split(",") for x in u.run(exe, a, b, cpus=6).strip().splitlines()]
        rust = u.run(crate / "target/release/ll_wire_bench", a, cpus=6).strip().split(",")
        want = L.arbitrate(L.packets(a), L.packets(b))
    arb = next(r for r in rows if r[0] == "arb")
    assert tuple(int(x) for x in arb[1:6]) == want, (arb, want)
    msgs = next(r for r in rows if r[0] == "messages")
    dec = [[r[1], r[2]] for r in rows if r[0] == "decode"] + [[rust[1], rust[2]]]
    meta = dict(cpus="6", source=SRC, input="60 s of the simulator's line A (ll_lines.record)",
                order_messages=msgs[1], all_messages=msgs[2])
    u.write_measured(OUT / "measured_decode.csv", ["key", "ns_per_msg"], dec, **meta)
    u.write_measured(OUT / "measured_arb.csv", ["packets", "messages", "gaps", "missing", "duplicates",
                                                "ns_per_packet"], [arb[1:]], **meta)


if __name__ == "__main__":
    main()
