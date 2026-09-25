"""Numbers gate: every numerical answer printed in Book 8, chapter 6 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_factors import correlations, ic, profitability, run, sml, value_signal  # noqa: E402

DATA = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-1"


def r(x, d=2):
    return round(float(x), d)


def rows(name):
    return list(csv.DictReader(open(DATA / name)))


def test_french_factors():
    s = {(x["factor"], x["period"]): x for x in rows("ff5_summary.csv")}
    g = lambda k, p, c="ann_mean": r(100 * float(s[(k, p)][c]), 1)  # noqa: E731
    sr = lambda k, p: r(float(s[(k, p)]["sharpe"]))  # noqa: E731
    assert (g("HML", "1963-2026"), sr("HML", "1963-2026"), r(float(s[("HML", "1963-2026")]["t"]))) == (3.6, 0.35, 2.77)
    assert (g("HML", "1963-2006"), g("HML", "2007-2020"), g("HML", "2021-2026")) == (5.7, -5.3, 9.4)
    assert (g("RMW", "1963-2026"), sr("RMW", "1963-2026"), g("RMW", "2007-2020"), sr("RMW", "2007-2020")) == \
        (3.1, 0.39, 2.8, 0.51)
    assert (g("CMA", "1963-2026"), g("CMA", "2007-2020"), g("Mkt-RF", "1963-2026")) == (3.0, -0.8, 7.2)
    c = {(x["period"], x["factor"]): x for x in rows("ff5_corr.csv")}
    assert (r(float(c[("1963-2026", "HML")]["RMW"])), r(float(c[("2007-2020", "HML")]["RMW"])),
            r(float(c[("1963-2026", "HML")]["Mom"])), r(float(c[("2007-2020", "HML")]["Mom"])),
            r(float(c[("1963-2026", "HML")]["CMA"])), r(float(c[("2007-2020", "HML")]["CMA"]))) == \
        (0.09, -0.14, -0.19, -0.48, 0.68, 0.49)
    d = rows("hml_drawdown.csv")[0]
    assert (d["peak"], d["trough"], r(100 * float(d["depth"]), 1), d["recovered"], r(100 * float(d["end_dd"]), 1)) == \
        ("200612", "202009", -57.8, "", -29.6)
    w = 1 + float(d["gain_to_peak"])
    assert (r(w), r((w - w * (1 + float(d["depth"]))) / (w - 1) * 100, 0)) == (9.77, 64)
    b = {x["portfolio"]: x for x in rows("beta_sml.csv")}
    assert (r(float(b["Lo 10"]["beta"])), r(100 * float(b["Lo 10"]["ann_excess"]), 1), r(float(b["Hi 10"]["beta"])),
            r(100 * float(b["Hi 10"]["ann_excess"]), 1)) == (0.59, 6.8, 1.6, 8.6)
    assert (r(100 * float(b["BAB"]["ann_excess"]), 1), r(float(b["BAB"]["sharpe"])), r(float(b["BAB"]["t"])),
            r(float(b["BAB"]["beta"])), b["BAB"]["start"]) == (4.3, 0.26, 1.95, -0.06, "196807")
    assert (r(0.594 * 7.19, 1), r(1.604 * 7.19, 1)) == (4.3, 11.5)


def test_synthetic():
    f = lambda k: (r(run(k)["sr"]), r(100 * run(k)["ret"], 1), r(100 * run(k)["vol"], 1), r(run(k)["beta"]),  # noqa: E731
                   r(100 * run(k)["alpha"], 1), r(run(k)["turnover"], 1))
    assert f("value") == (-0.07, -0.7, 10.2, -0.11, 0.4, 3.2)
    assert f("value_annual") == (0.21, 1.9, 9.2, -0.12, 3.1, 2.5)
    assert f("ff") == (0.24, 2.2, 9.2, -0.12, 3.4, 2.5)
    assert f("lookahead") == (-0.06, -0.6, 10.2, -0.11, 0.5, 3.2)
    assert f("profitability") == (-1.03, -3.8, 3.7, 0.0, -3.8, 2.1)
    assert f("bab") == (-0.52, -5.4, 10.4, 0.18, -7.3, 8.2)
    assert f("composite") == (0.44, 4.0, 9.0, 0.01, 3.9, 5.1)
    s = sml()
    assert [(r(x["beta"]), r(100 * x["ret"], 1)) for x in (s[0], s[-1])] == [(0.49, 2.4), (1.39, 13.4)]
    c = correlations()
    assert (r(c["value_profitability"]), r(c["value_momentum"]), r(c["value_bab"])) == (-0.6, -0.56, 0.49)
    assert (r(ic(value_signal("pit")), 3), r(ic(value_signal("ff")), 3), r(ic(profitability()))) == (1.0, 0.991, -0.29)


def test_exercises():
    assert (r(1 / 0.6), r(1 / 1.5), r(1 / 0.6 - 1 / 1.5)) == (1.67, 0.67, 1.0)
    assert r(100 * (0.5 * 1.75 * 0.03 * 2), 2) == 5.25 and r(10 / 14**0.5, 1) == 2.7
    assert (r(9.77 * (1 - 0.578), 2), r(6.8 - 4.3, 1), r(11.5 - 8.6, 1)) == (4.12, 2.5, 2.9)
    assert r(0.3 / (0.5 * (2 + 2 * -0.5) ** 0.5), 2) == 0.6 and r((2 * 0.09 / (1 - 0.5)) ** 0.5, 2) == 0.6
