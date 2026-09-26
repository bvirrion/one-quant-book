"""Chapter 18 measured data (not a fig_*.py): the C++ handler's time per input on the minute of ll_feed (checked to
publish exactly what the Python reference publishes), and the receive buffer's capacity in datagrams when the reader
stalls during a burst, by SO_RCVBUF and payload. Outputs measured_handle.csv and measured_rcvbuf.csv."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_feed as L  # noqa: E402

sys.path.insert(0, str(L.ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

OUT = L.ROOT / "figdata/low-latency/18-the-feed-handler"
SRC = "code/low-latency/18-the-feed-handler/cpp/ll_feed_bench.cpp"


def main():
    exe = u.compile_cpp(HERE.parent / "cpp/ll_feed_bench.cpp", includes=[L.ROOT / "code/firm/feedhandler/cpp"])
    with tempfile.TemporaryDirectory() as d:
        files = dict(zip(("lineA", "lineB", "clean", "snapshot"), L.minute(), strict=True))
        for k, v in files.items():
            (pathlib.Path(d) / f"{k}.bin").write_bytes(v)
        out = u.run(exe, "handle", *(pathlib.Path(d) / f"{k}.bin" for k in files), cpus=6).strip().splitlines()
    ref = L.fh.Handler(retx=L.fh.RetxServer(L.fh.recorded(files["clean"]), window=100_000)).run(
        L.fh.merge(files["lineA"], files["lineB"], files["snapshot"]))
    ev = next(x.split(",") for x in out if x.startswith("events"))
    assert int(ev[1]) == len(ref.events) and int(ev[2], 16) == ref.hash, (ev, len(ref.events), hex(ref.hash))
    rows = [x.split(",")[1:] for x in out if x.startswith("handle")]
    inputs = next(x.split(",")[1] for x in out if x.startswith("inputs"))
    u.write_measured(OUT / "measured_handle.csv", ["quantile", "ns"], rows, cpus="6", source=SRC, inputs=inputs,
                     events=ev[1], input_data="ll_feed.minute(): 60 s from the open, impaired lines, retransmission on")
    rc = []
    for size in (64, 1000):
        for x in u.run(exe, "rcvbuf", 50_000, size).strip().splitlines():
            _, payload, asked, granted, received = x.split(",")
            rc.append([payload, asked, granted, received, f"{int(granted) / max(int(received), 1):.0f}"])
    u.write_measured(OUT / "measured_rcvbuf.csv", ["payload", "asked", "granted", "held", "bytes_per_datagram"], rc,
                     source=SRC, burst="50,000 datagrams on loopback while the reader is stalled",
                     rmem_max=pathlib.Path("/proc/sys/net/core/rmem_max").read_text().strip())


if __name__ == "__main__":
    main()
