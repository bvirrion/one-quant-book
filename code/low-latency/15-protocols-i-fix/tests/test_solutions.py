"""Numbers gate, Book 13 chapter 15."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
import ll_fix as f  # noqa: E402

fx = f.fx
FIG = ROOT / "figdata/low-latency/15-protocols-i-fix"


def measured():
    with open(FIG / "measured_fix.csv", newline="", encoding="utf8") as fh:
        return {r["key"]: float(r["ns_per_msg"]) for r in csv.DictReader(fh)}


def test_short_trace_is_current():
    lines = (ROOT / "code/firm/fixengine/data/expected_trace.txt").read_text().splitlines()
    assert (HERE / "python/trace_short.txt").read_text().splitlines() == [f.short(x) for x in lines]


def test_published_example_and_exercises():
    ex = (ROOT / "code/firm/fixengine/data/wikipedia_example.fix").read_text().strip().encode().replace(b"|", fx.SOH)
    body = ex[ex.index(b"35="):ex.index(b"10=")]
    assert len(body) == 5 + 10 + 10 + 7 + 21 + 5 + 7 == 65
    assert sum(ex[:ex.index(b"10=")]) == 4158 and 4158 % 256 == 62
    hb = fx.encode(b"0", [], 2, "A", "B", 52_200_000)
    assert b"9=45\x01" in hb and hb.endswith(b"10=075\x01")                              # exercise 1
    swapped = fx.encode(b"0", [], 2, "B", "A", 52_200_000)
    assert swapped != hb and fx.checksum(swapped[:-7]) == fx.checksum(hb[:-7]) == 75     # exercise 4
    assert f.detection_s(30) == 66 and 1.2 * 30 == 36                                    # exercise 2


def test_weekend_gap():
    busy = f.sender_stream(200, f.detection_s(30), 30)
    assert len(busy) == 13_227 and busy.count("0") == 0
    assert f.resend_count(busy) == f.resend_count(busy, gap_fill=False) == 13_227
    assert 13_227 * 205 == 2_711_535 and round(2_711_535 * 8 / 1e9 * 1e3, 1) == 21.7
    wk = f.sender_stream(1 / 3600, 48 * 3600, 30)
    assert len(wk) == 5776 and wk.count("8") == 38
    assert f.resend_count(wk) == 77 and f.resend_count(wk, gap_fill=False) == 5776
    m = measured()
    c, p = m["view"] * 1e-9, m["python"] * 1e-9
    assert round(f.resync_s(13_227, 205, 1e9, c, 1e-3) * 1e3, 1) == 24.8
    assert round(f.resync_s(13_227, 205, 1e9, p, 1e-3) * 1e3) == 94
    assert round(f.resync_s(77, 205, 1e9, p, 1e-3) * 1e3, 1) == 2.5
    assert round(f.resync_s(5776, 205, 1e9, p, 1e-3) * 1e3) == 42
    assert len(f.sender_stream(200, f.detection_s(1), 1)) == 447                          # 1-second heartbeat


def test_measured():
    m = measured()
    assert 40 < m["view"] < 160 and round(m["view"], -1) == 80                            # ~80 ns
    assert 500 < m["map"] < 1800 and 8 < m["map"] / m["view"] < 16                        # ~900 ns, ~11x
    assert 2500 < m["python"] < 9000 and round(m["python"] / 1000, 1) == 5.3              # ~5 us
    assert round(m["builder"], -1) == 60 and round(m["concat"], -1) == 330 and m["concat"] / m["builder"] > 4
    assert round(m["map"] / m["view"]) == 11 and round(m["view"]) == 84 and round(m["map"]) == 892
    assert round(1e9 / m["view"] / 1e6) == 12                                             # some twelve million a second
    assert round(2e5 * m["view"] * 1e-9 * 100, 1) == 1.7 and round(2e5 * m["map"] * 1e-9 * 100) == 18   # exercise 6
    assert round(2e5 * m["python"] * 1e-9 * 100) == 107
