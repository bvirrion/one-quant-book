"""Numbers gate: every numerical answer printed in Book 9, chapter 7 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_tailhedge import bleed, market, portfolios, real, table  # noqa: E402


def pct(x, d=1):
    return round(100 * float(x), d)


def test_portfolios():
    got = {k: (pct(v["growth"]), pct(v["vol"]), pct(v["max_dd"], 0), pct(v["worst_month"], 0)) for k, v in table().items()}
    assert got == {"index": (3.0, 19.0, -73, -43), "5% monthly": (2.5, 13.9, -41, -17), "10% monthly": (3.2, 16.0, -49, -22),
                   "10% quarterly": (3.0, 14.0, -46, -24), "20% quarterly": (4.2, 16.2, -52, -33),
                   "10% quarterly, monetised at 3x": (2.2, 14.0, -62, -26), "20% half-yearly": (4.6, 15.5, -50, -36),
                   "70% index, 30% cash": (2.8, 13.2, -58, -31), "index + trend overlay": (6.3, 17.6, -56, -24)}
    assert portfolios()["10% quarterly, monetised at 3x"]["monetised"] == 11


def test_bleed():
    got = {k: (pct(v["bleed"]), [pct(x) for x in v["crash_years"]]) for k, v in bleed().items()}
    assert got == {"5% monthly": (-6.0, [19.2, -2.7, 39.5]), "10% monthly": (-3.9, [15.2, -3.7, 29.2]),
                   "10% quarterly": (-3.8, [11.8, -8.1, 21.9]), "20% quarterly": (-1.7, [6.6, -5.1, 20.6]),
                   "10% quarterly, monetised at 3x": (-3.6, [16.3, 0.4, 5.0]), "20% half-yearly": (-1.5, [2.0, -2.1, 26.3])}
    _, sim = market()
    assert [s // 252 for s, _ in sim["crashes"]] == [5, 12, 17]


def test_real():
    x = real()
    got = {n: (pct(float(x[n]["ann_log"])), pct(float(x[n]["vol"])), pct(float(x[n]["max_dd"])), x[n]["dd_peak"],
               x[n]["dd_trough"], pct(float(x[n]["oct_1987"])), pct(float(x[n]["autumn_2008"])),
               pct(float(x[n]["covid_2020"])), pct(float(x[n]["worst_21d"]))) for n in ("PPUT", "CLLZ", "SPX")}
    assert got == {"PPUT": (7.7, 13.5, -42.0, "2007-07-19", "2009-03-09", -10.6, -6.7, -0.4, -13.5),
                   "CLLZ": (7.8, 14.6, -47.2, "2007-10-12", "2009-03-09", -17.1, -31.2, -17.9, -30.0),
                   "SPX": (8.5, 18.4, -56.8, "2007-10-09", "2009-03-09", -21.8, -30.1, -19.9, -33.0)}


def test_crash_windows_and_exercises():
    from s2_tailhedge import crash_windows
    c = crash_windows()
    assert [pct(x["pnl"]) for x in c] == [30.0, 12.0, 29.2] and pct(c[1]["vol_before"]) == 3.9
    assert round(17 * -6.0 + 19.2 - 2.7 + 39.5, 1) == -46.0 and 3 * 1.0 == 3.0


def test_slow_bear():
    from s2_tailhedge import slow_bear
    x = slow_bear()
    assert (pct(x["index"]), pct(x["static"]), pct(x["puts"])) == (-28.7, -21.0, -32.4)
