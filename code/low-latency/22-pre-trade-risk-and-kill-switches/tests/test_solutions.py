"""Numbers gate, Book 13 chapter 22."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = ROOT / "figdata/low-latency/22-pre-trade-risk-and-kill-switches"
sys.path.insert(0, str(HERE / "python"))
import ll_risk as L  # noqa: E402

rg, ra = L.rg, L.ra


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def test_exercises():
    lim = rg.Limits.from_dict({"version": 1, "max_age_ns": 10**15, "ref_max_age_ns": 10**15, "dup_ns": 0,
                               "firm": {"max_gross": 10**18}, "desks": {"D": {"max_gross": 10**18}},
                               "strategies": {"S": {"desk": "D", "rate": 10**6, "burst": 10**6, "max_open": 100}},
                               "instruments": {"1": {"collar_bp": 500, "max_qty": 10**6, "max_notional": 10**15,
                                                     "max_long": 5_000, "max_short": 10**6}}})
    g = rg.Gate(lim, 0)
    g.set_reference(0, 1, 250_000)
    codes = [g.check(k, "S", 1, side, 1, p, 100 + k)[0]
             for k, (side, p) in enumerate((("B", 262_500), ("B", 262_600), ("S", 237_500), ("S", 237_400)))]
    assert codes == [".", "C", ".", "C"]
    for cl in list(g.orders):
        g.on_done(cl)
    g.pos[1] = 2_000
    assert g.check(10, "S", 1, "B", 1_500, 250_000, 1)[0] == "." and g.check(11, "S", 1, "B", 1_000, 250_100, 2)[0] == "."
    assert g.check(12, "S", 1, "B", 600, 250_200, 3)[0] == "L" and g.check(13, "S", 1, "B", 500, 250_300, 4)[0] == "."
    assert round(L.rate_per_s()) == 1_481 and round(L.shares_per_execution()) == 99
    assert round(26 / 1000 * 100) == 3


def test_table_and_problem():
    r = {x["config"]: x for x in rows("runaway.csv")}
    n = r["none"]
    assert (int(n["sent"]), int(n["position"]), int(n["shares_45min"])) == (7_500, 750_000, 405_000_000)
    for k in ("collar", "size and notional"):
        assert r[k]["sent"] == n["sent"] and r[k]["position"] == n["position"]
    t = r["throttle"]
    assert (int(t["sent"]), int(t["position"]), int(t["shares_45min"])) == (2_545, 254_500, 135_000_000)
    assert round(float(t["first_refusal_ms"])) == 40 and int(t["last_second"]) == 500
    d = r["duplicates"]
    assert (int(d["sent"]), int(d["position"]), int(d["last_second"])) == (55, 5_500, 11)
    assert round(int(d["shares_45min"]) / 1e6, 1) == 3.0
    f, p = r["position (fills only)"], r["position (in flight)"]
    assert (int(f["sent"]), int(f["position"]), round(float(f["first_refusal_ms"]))) == (210, 21_000, 140)
    assert (int(p["sent"]), int(p["position"]), round(float(p["first_refusal_ms"]))) == (200, 20_000, 130)
    assert int(p["refused"]) == 7_300
    c = r["capital threshold"]
    assert (int(c["sent"]), int(c["position"]), round(float(c["first_refusal_ms"]))) == (249, 24_900, 160)
    assert r["position + kill switch"]["position"] == p["position"]
    s = ra.run(ra.CONFIGS["none"], 5.0)
    assert s.last_price == 1_074_900 and round((s.last_price / ra.START - 1) * 100, 1) == 7.5
    assert (s.last_price - ra.START) // ra.TICK == 749
    assert 1_500 * 100 * 2_700 == 405_000_000 and 500 * 100 * 2_700 == 135_000_000
    assert 154 * 20_000 == 3_080_000


def test_fixture_stale_count():
    head = (ROOT / "code/firm/riskgate/data/expected.txt").read_text().splitlines()[0]
    assert "S:50," in head and head.split()[1] == "4874"


def test_measured():
    m = {(x["case"], float(x["quantile"])): float(x["ns"]) for x in rows("measured_check.csv")}
    assert round(m[("all accepted", 0.5)]) == 11
    extra = m[("all accepted: duplicate check on", 0.5)] - m[("all accepted", 0.5)]
    assert 6 <= extra <= 14 and round(extra, -1) == 10
    assert round(m[("fixture: all", 0.5)]) == 26 and round(26 / 1000 * 100) == 3
    assert abs(m[("fixture: accepted", 0.5)] - m[("fixture: refused", 0.5)]) < 3      # no cheaper, no dearer
    rtt = {x["transport"]: float(x["p50"]) for x in csv.DictReader(open(
        ROOT / "figdata/low-latency/12-queues-ring-buffers-and-shared-memory/measured_rtt.csv"))}
    assert round(rtt["SPSC over shared memory"], -2) == 200 and round(200 / 26) == 8
