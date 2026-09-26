"""Numbers gate, Book 13 chapter 18."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_feed as L  # noqa: E402

FIG = L.ROOT / "figdata/low-latency/18-the-feed-handler"


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def test_minute_figure_numbers():
    s = {r["run"]: r for r in rows("summary.csv")}
    r, n = s["retx"], s["snapshot"]
    assert (r["gaps"], r["filled_by_line"]) == ("4232", "4224") and int(r["gaps"]) - int(r["filled_by_line"]) == 8
    assert float(r["worst_ms"]) == 2.7
    assert n["snapshots"] == "7" and round(float(n["stale_ms"]) / 1000) == 5
    long = [float(x["ms"]) for x in rows("stale_snapshot.csv") if float(x["ms"]) > 100]
    assert len(long) == 7 and 300 < min(long) and max(long) < 1000
    rate = [int(x["messages"]) for x in rows("rate.csv")]
    assert max(rate) > 9000 / 10 and round(max(rate) / (sum(rate[295:305]) / 10)) == 16
    assert int(r["events"]) == sum(rate) + 3                         # the three events published before the open


def test_exercises():
    assert 262144 * 2 == 524288 and round(524288 / 960) == 546                            # exercise 2
    assert L.snapshot_staleness(0.5, 0.005) == (0.255, 0.505)                             # exercise 3
    q = L.backlog(2e6, 1.2e6, 0.03)
    assert round(q) == 24_000 and round(q * 960 / 1e6) == 23 and round(L.rcvbuf_needed(q, 960) / 1e6, 1) == 11.5


def test_problem():
    q = L.backlog(1.5e6, 0.5e6, 0.02)
    assert round(q) == 20_000 and round(q / 3e5 * 1e3) == 67 and q * 2e-6 == 0.04
    assert q * 960 == 19_200_000 and L.rcvbuf_needed(q, 960) == 9_600_000 > 4 * 2**20
    assert 20_000 - 8_738 == 11_262 and -(-11_262 // 1000) == 12
    assert L.snapshot_staleness(1.0) == (0.5, 1.0)
    assert round(1 / 1.5e6 * 1e9) == 667


def test_measured():
    rc = [r for r in rows("measured_rcvbuf.csv")]
    for r in rc:
        assert int(r["granted"]) == 2 * int(r["asked"])                                   # the kernel doubles
    small = {int(r["asked"]): int(r["held"]) for r in rc if r["payload"] == "64"}
    big = {int(r["asked"]): int(r["held"]) for r in rc if r["payload"] == "1000"}
    assert small[4194304] == 8738 and small[262144] == 546 and round(8388608 / small[4194304]) == 960
    assert round(8388608 / big[4194304]) == 2305
    h = {float(r["quantile"]): float(r["ns"]) for r in rows("measured_handle.csv")}
    assert 20 < h[0.5] < 120 and round(h[0.5]) == 39
    assert round(h[0.99], -1) == 160 and round(h[0.999], -1) == 290
    assert round(9300 * h[0.5] * 1e-9 * 100, 2) == 0.04                               # busy 0.04% of the time
