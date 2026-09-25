"""Numbers gate: every numerical answer printed in Book 8, chapter 5 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_momentum import DATA, betas, french, scaled, summary  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_french():
    rows, worst = french()
    raw, sc = rows["raw"], rows["scaled"]
    f = lambda row, k, d=1: r(100 * float(row[k]), d)  # noqa: E731
    assert (f(raw, "ann_mean"), f(raw, "ann_vol"), r(float(raw["sharpe"])), r(float(raw["skew"])),
            r(float(raw["exkurt"]), 1)) == (7.4, 16.3, 0.45, -3.02, 27.3)
    assert (f(sc, "ann_mean"), f(sc, "ann_vol"), r(float(sc["sharpe"])), r(float(sc["skew"])),
            r(float(sc["exkurt"]), 1)) == (15.4, 17.7, 0.87, -0.4, 3.1)
    assert (f(raw, "worst"), raw["worst_month"], f(sc, "worst"), sc["worst_month"]) == (-52.6, "193208", -29.1, "193909")
    assert (f(raw, "maxdd"), raw["dd_peak"], raw["dd_trough"], f(sc, "maxdd"), sc["dd_trough"]) == \
        (-78.4, "193206", "193909", -42.5, "193305")
    assert (f(raw, "mar_may_2009"), f(sc, "mar_may_2009"), f(raw, "year_2009"), f(sc, "year_2009")) == \
        (-49.4, -16.5, -52.8, -16.8)
    assert (raw["start"], raw["months"]) == ("192705", "1191")
    w = {x["month"]: x for x in worst}
    assert (f(w["200904"], "raw"), f(w["200904"], "scaled"), r(float(w["200904"]["weight"]))) == (-34.4, -10.1, 0.29)
    assert (f(w["193208"], "scaled"), r(float(w["193208"]["weight"])), r(float(w["193909"]["weight"]))) == \
        (-22.0, 0.42, 0.92)
    ann = {int(x["year"]): x for x in csv.DictReader(open(DATA / "mom_annual.csv"))}
    assert (f(ann[1932], "raw"), f(ann[1932], "scaled"), f(ann[2023], "raw")) == (-64.5, -29.3, -20.5)
    assert r((1 - 0.118) * (1 - 0.3436) * (1 - 0.1254) - 1, 3) == -0.494


def test_synthetic_books():
    got = {k: summary(k) for k in ("total", "residual", "industry")}
    t = lambda s: (r(s["sr_gross"]), r(s["sr_net"]), r(100 * s["ret_net"], 1), r(100 * s["vol"], 1),  # noqa: E731
                   r(100 * s["maxdd"], 0), r(s["turnover"], 1), r(s["ic"], 3))
    assert t(got["total"]) == (0.39, 0.31, 4.1, 13.4, -40, 5.7, 0.02)
    assert t(got["residual"]) == (0.55, 0.45, 4.9, 11.0, -33, 5.4, 0.023)
    assert t(got["industry"]) == (-0.04, -0.23, -1.4, 6.4, -23, 5.9, 0.001)
    b = betas("total")
    assert (r(b["bear"]), r(b["bull"]), r(100 * b["bear_days"], 1)) == (0.22, 0.11, 6.7)
    s = scaled("total")
    assert (r(s["sr_raw"]), r(s["sr_scaled"]), r(100 * s["dd_raw"], 0), r(100 * s["dd_scaled"], 0)) == (0.52, 0.52, -30, -25)
    s = scaled("residual")
    assert (r(s["sr_raw"]), r(s["sr_scaled"])) == (0.67, 0.7)


def test_exercises():
    assert r(0.12 / 0.40, 2) == 0.3 and r(0.3 * -0.34, 3) == -0.102
    assert r(1 / 0.5 - 1, 1) == 1.0 and r(0.5 * 2 - 1, 1) == 0.0
    assert r(5.7 * 0.001 * 2 * 100, 2) == 1.14
