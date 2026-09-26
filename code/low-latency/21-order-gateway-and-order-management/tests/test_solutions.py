"""Numbers gate, Book 13 chapter 21."""
import csv
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = ROOT / "figdata/low-latency/21-order-gateway-and-order-management"
sys.path.insert(0, str(HERE / "python"))
import ll_gateway as L  # noqa: E402

gw = L.gw


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def test_exercises():
    b = gw.TokenBucket(300, 2)
    assert [b.allow(t * 1_000_000) for t in (0, 0, 0, 1, 4, 5)] == [True, True, False, False, True, False]
    g = gw.Gateway(max_long=500)
    g.position = 200
    for cl in (1, 2):
        g.new(0, cl, "B", 100, 1000)
        g.on_report(0, "A", cl)
    assert g.worst_long() == 400
    assert g.replace(0, 1, 3, 300, 1000) == ("refused", "exposure")
    assert g.replace(0, 1, 3, 200, 1000)[0] == "send" and g.worst_long() == 500
    p = L.race_rested(50, 300e-6, 50e-6)
    assert round(p * 100, 1) == 1.7 and round(20_000 * p) == 347


def test_race_formula_and_problem():
    assert [round(L.race_rested(200, us * 1e-6) * 100, 2) for us in (10, 100, 1000)] == [0.60, 2.37, 18.45]
    assert round(40_000 * L.race_rested(200, 100e-6), -1) == 950
    assert round(40_000 * L.race_exact(200, 100e-6, 1e-3), -1) == 880
    for us in (1, 100, 10_000):                         # long holds: lam W / (1 + lam W), below 1 - e^{-lam W}
        lw = 200 * (us + 20) * 1e-6
        assert abs(L.race_exact(200, us * 1e-6, 1e3) - lw / (1 + lw)) < 1e-3
        assert L.race_exact(200, us * 1e-6, 1e-3) < L.race_rested(200, us * 1e-6)
    # the exact formula against a direct numerical integration
    lam, hold, w = 200.0, 1e-3, 1.02e-3
    n, num, den = 200_000, 0.0, 0.0
    for i in range(n):
        h = (i + 0.5) * 40 * hold / n
        dens = math.exp(-h / hold) / hold
        surv = math.exp(-lam * max(0.0, h - w))
        num += dens * surv * (1 - math.exp(-lam * min(h, w)))
        den += dens * surv
    assert abs(num / den - L.race_exact(lam, 1e-3, hold)) < 1e-4


def test_figure_data():
    r = {int(x["latency_us"]): x for x in rows("races.csv")}
    sim = {k: float(v["simulated"]) for k, v in r.items()}
    assert round(sim[10] * 100, 2) == 0.65 and round(sim[100] * 100, 1) == 2.1 and round(sim[1000] * 100, 1) == 11.7
    assert round(float(r[100]["exact"]) * 100, 1) == 2.2 and round(float(r[3000]["exact"]) * 100) == 16
    for k, v in r.items():                             # the engine agrees with the exact formula everywhere
        n = int(v["cancels"])
        sd = math.sqrt(float(v["exact"]) * (1 - float(v["exact"])) / n)
        assert abs(sim[k] - float(v["exact"])) < 3 * sd + 1e-3, k


def test_fixture_numbers():
    j = (ROOT / "code/firm/ordergw/data/journal_cancel.txt").read_text().splitlines()
    cancels = sum(1 for x in j if " Q X " in x and x.endswith("send"))
    exp = (ROOT / "code/firm/ordergw/data/expected.txt").read_text()
    assert cancels == 245 and "races 6 " in exp.splitlines()[0]
    assert "refused 111/" in exp.splitlines()[1]
    mean = 245 * L.race_exact(200, 100e-6, 1e-3)
    assert round(mean, 1) == 5.4 and round(math.sqrt(mean), 1) == 2.3


def test_measured():
    m = {(x["step"], float(x["quantile"])): float(x["ns"]) for x in rows("measured_messages.csv")}
    med = [v for (s, q), v in m.items() if q == 0.5]
    p99 = [v for (s, q), v in m.items() if q == 0.99]
    assert 3.5 <= min(med) and max(med) <= 5.5 and 4.5 <= min(p99) and max(p99) <= 6.5
    e = {int(x["open_orders"]): x for x in rows("measured_exposure.csv")}
    assert round(float(e[1000]["array_ns"]) / 1000, 1) == 0.4 and round(float(e[1000]["map_ns"]) / 1000, 1) == 1.6
    assert round(float(e[1000]["map_ns"]) / 5, -2) == 300                                   # some three hundred times
    assert all(float(x["sums_ns"]) < 3 for x in e.values())
