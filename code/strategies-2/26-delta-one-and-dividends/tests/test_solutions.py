"""Numbers gate: every numerical answer printed in Book 9, chapter 26 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "deltaone"))
from firm_deltaone import index_arb  # noqa: E402
from s2_deltaone import arbitrage, dividends, exposure, financing, market  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_arbitrage():
    a = arbitrage()
    got = [(a[k]["trades"], r(a[k]["mean"], 2), r(a[k]["total"], 0), r(100 * a[k]["win"])) for k in (0, 1, 2, 5)]
    assert got == [(2230, 1.64, 3657, 100.0), (2230, 1.14, 2539, 69.2), (2230, 0.77, 1707, 60.7), (2230, -0.26, -584, 46.9)]
    assert a["band"] == 5.0
    cfg, sim = market()                                                                     # exercise 7
    assert [r(index_arb(sim, cfg, k)["pnl"].mean(), 2) for k in (3, 4)] == [0.4, 0.05]


def test_financing():
    f = financing()
    assert (r(100 * f[0]["taken"], 1), r(f[0]["locked"]), r(f[0]["annual"])) == (10.0, 15.4, 0.4)
    assert (r(100 * f[55]["taken"], 1), r(f[55]["locked"]), r(f[55]["annual"])) == (67.5, 40.7, 8.0)
    assert f["hurdle"] == 15.0


def test_exposure():
    e = exposure()
    assert (r(e["price"], 2), r(e["issuer_gain"], 2), r(e["expected_life"], 2)) == (101.84, 0.11, 2.66)
    assert r(e["issuer_gain"] / 100 * 1e9 / 1e6) == 1.1


def test_dividends():
    d = dividends()
    assert [r(x) for x in d["expected"]] == [100.8, 104.7, 108.7, 112.9, 117.2]
    assert [r(x) for x in d["futures"]] == [96.7, 96.3, 95.7, 94.9, 93.7]
    assert [r(100 * x) for x in d["mean"]] == [4.2, 3.9, 3.8, 3.9, 3.9]
    assert [r(100 * x) for x in d["sd"]] == [12.3, 9.1, 7.5, 6.6, 5.9]
    assert [r(100 * x) for x in d["q05"]] == [-25.5, -13.2, -9.4, -8.6, -7.1]
    assert [r(100 * x) for x in d["loss"]] == [20.9, 25.2, 29.8, 28.0, 24.6]
    assert (r(d["corr"], 2), r(100 * d["recession_return"])) == (0.41, -24.4)


def test_exercises():
    assert r((7 - 5) * 1e-4 * 50e6, 0) == 10000                                           # exercise 1
    assert r(((40 - 15) * 0.25 - 5) * 1e-4 * 100e6, 0) == 12500                           # exercise 2
    assert (r(100 * (108.7 / 95.7 - 1)), r(100 * ((108.7 / 95.7) ** (1 / 3) - 1))) == (13.6, 4.3)   # exercise 3
