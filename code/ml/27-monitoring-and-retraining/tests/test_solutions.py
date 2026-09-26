"""Numbers gate: every numerical answer printed in Book 12, chapter 27 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_monitor as m  # noqa: E402

NEVER = m.DAYS - m.START


def test_setup_and_thresholds():
    b, _, _, thr, _ = m.model()
    assert m.N == 200 and m.K == 5 and m.TRAIN == 60 and m.DAYS == 400 and m.START == 200
    assert m.BETA.tolist() == [0.08, -0.06, 0.05, 0.0, 0.0] and abs(m.RATE - 1 / 21) < 1e-12
    th = m.thresholds()
    assert (round(th["feature PSI"], 3), round(th["feature KS"], 3), round(th["prediction PSI"], 3),
            round(th["inside threshold"], 2)) == (0.115, 0.115, 0.089, 0.07)
    k, h, target = th["IC CUSUM"]
    assert (round(k, 3), round(h, 2), round(target, 3)) == (0.035, 0.11, 0.103)
    assert round(h / m.ic_levels()["sd"], 1) == 1.6                       # "about one and a half days' sd"
    assert th["feature PSI"] > 0.10


def test_ic_levels_and_days_to_see():
    L = m.ic_levels()
    assert (round(L["before"], 3), round(L["sd"], 3)) == (0.103, 0.071)
    assert (round(L["reversal"], 3), round(L["unit change"], 3), round(L["slow fade"], 3)) == (0.003, 0.087, 0.081)
    d = {f: m.days_to_see(L["before"] - L[f], L["sd"]) for f in ("reversal", "unit change", "slow fade")}
    assert (round(d["reversal"]), round(d["unit change"], -1), round(d["slow fade"], -1)) == (4, 150, 80)
    assert round(L["before"] - L["unit change"], 4) == 0.0168
    assert round(m.days_to_see(0.0168, 0.022)) == 15 and round(0.071 / np.sqrt(10), 3) == 0.022
    assert round(m.days_to_see(0.02, 0.07)) == 105


def test_delays_table():
    d = m.delays()
    want = {
        "none": {"feature PSI": (12, NEVER), "feature KS": (10, NEVER), "prediction PSI": (17, NEVER),
                 "inside threshold": (11, NEVER), "IC CUSUM": (13, NEVER)},
        "unit change": {"feature PSI": (0, 0), "feature KS": (0, 0), "prediction PSI": (0, 0),
                        "inside threshold": (0, 0), "IC CUSUM": (9.5, NEVER)},
        "reversal": {"feature PSI": (12, NEVER), "feature KS": (10, NEVER), "prediction PSI": (17, NEVER),
                     "inside threshold": (11, NEVER), "IC CUSUM": (1, 0)},
        "slow fade": {"feature PSI": (12, 42), "feature KS": (8, 60), "prediction PSI": (19.5, NEVER),
                      "inside threshold": (9.5, NEVER), "IC CUSUM": (13, NEVER)},
    }
    for f, row in want.items():
        for mon, (first, sus) in row.items():
            assert d[(f, mon)][:2] == (first, sus), (f, mon, d[(f, mon)])
    blind = [d[("none", mon)][0] for mon in m.MONITORS]
    assert min(blind) == 10 and max(blind) == 17
    for mon in m.MONITORS:                                               # false pages near 1 in 21 before day 200
        assert abs(d[("none", mon)][2] - 1 / 21) < 0.01


def test_reversal_and_unit_change_details():
    th = m.thresholds()
    first = [m.first_alarm(*m._alarm_series(r, "IC CUSUM", th), m.START) for r in m.runs("reversal")]
    assert sum(x <= 1 for x in first) == 13
    uc = m.runs("unit change")
    assert round(np.mean([r["feature PSI"][m.START:].mean() for r in uc])) == 7
    assert round(np.mean([r["feature PSI"][m.START:].mean() for r in uc]) / th["feature PSI"], -1) == 60
    inside = np.mean([r["share inside"][m.START:].mean() for r in uc])
    assert round(inside, 2) == 0.63 and round(np.mean([r["share inside"][:m.START].mean() for r in uc]), 2) == 0.50
    assert round((inside - 0.5) / 0.5, 2) == 0.26                         # a quarter fewer names traded


def test_fade_alarm_rates():
    r = m.alarm_rates("slow fade")
    assert all(v[:8].mean() < 1.3 for v in r.values())                  # about one alarm day a month before day 200
    assert r["feature PSI"][-1] > 20 and r["IC CUSUM"].max() < 3


def test_shadow_and_rollback():
    s = m.shadow()
    assert (s["median days"], s["max days"], s["promoted"]) == (10.0, 19, 20)
    assert (round(s["challenger IC"], 3), round(s["champion IC"], 3), round(s["challenger b1"], 3)) == (0.105, 0.003, -0.081)
    fp, deficit = m.false_promotions()
    assert fp == 0.02 and m.false_promotions(min_days=3)[0] == 0.16
    assert round(float(m.shadow_run(1, min_days=3)[4][2]), 7) == 1.3e-6
    rb = m.rollbacks()
    assert (rb["median days"], rb["max days"]) == (3.0, 18.0)
    assert (round(rb["cost full"], 2), round(rb["cost canary"], 3)) == (0.26, 0.026)


def test_pooled_exercise():
    p = m.pooled()
    assert round(p["threshold"], 4) == 0.0056 and round(p["days per page"], 1) == 3.7
    assert p["slow fade"][0] == 15.5 and p["none"] == (18.0, 20.0) and p["unit change"] == (0.0, 0.0)
    assert p["month in alarm, fade"] == (22.5, 120.0) and p["false months"] == 4
    assert round(m.thresholds()["feature PSI"] / p["threshold"], -1) == 20
