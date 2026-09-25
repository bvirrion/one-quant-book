"""Numbers gate: every numerical answer printed in Book 9, chapter 1 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_vrp import atm_iv, implementations, leverage_table, market, real, stats  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_implementations():
    imp, starts = implementations()
    got = {k: (r(stats(x)["sr"]), r(stats(x)["skew"]), r(stats(x)["worst_sd"], 1), r(100 * stats(x)["share_up"], 0))
           for k, x in imp.items()}
    assert got == {"short variance": (0.69, -3.53, -7.7, 79), "hedged straddle": (1.24, -2.32, -6.4, 77),
                   "overwrite": (0.4, -4.24, -8.1, 69), "put write": (0.08, -7.22, -10.2, 92),
                   "variance, 1/strike": (0.09, -12.45, -14.2, 79), "index": (0.26, -1.82, -6.8, 62)}
    assert len(starts) == 239 and r(100 * imp["hedged straddle"].mean()) == 0.53
    assert stats(imp["short variance"])["worst_at"] == 71 and r(71 * 21 / 252, 1) == 5.9
    cfg, S = market()
    assert (r(S["r"].std() * math.sqrt(252), 3), r(np.mean(atm_iv(S["v"], cfg, 21 / 252)), 3)) == (0.19, 0.183)


def test_leverage():
    got = {k: (r(v["sr_before"]), r(100 * v["worst"], 1), v["dead"]) for k, v in leverage_table().items()}
    assert got == {0.05: (1.57, -11.1, False), 0.1: (1.57, -22.2, False), 0.2: (1.57, -44.3, False),
                   0.4: (1.57, -88.6, False), 0.6: (1.57, -132.9, True)}


def test_real():
    s, worst, w = real()
    assert (s["months"], s["first"], s["last"]) == ("440", "1990-01-31", "2026-08-21")
    assert (r(100 * float(s["mean_vix"]), 1), r(100 * float(s["mean_rv"]), 1), r(100 * float(s["share_above"]), 0),
            r(100 * float(s["mean_gap"]), 1)) == (19.5, 15.4, 84, 4.1)
    assert [(x["month_end"], r(100 * float(x["vix"]), 1), r(100 * float(x["realised"]), 1)) for x in worst[:4]] == \
        [("2020-02-28", 40.1, 94.5), ("2008-09-30", 39.4, 82.3), ("2008-08-29", 20.6, 54.3), ("2025-03-31", 22.3, 47.7)]
    got = {k: (r(100 * float(v["ann_return"]), 1), r(100 * float(v["ann_vol"]), 1), r(float(v["sharpe"])),
               r(100 * float(v["max_dd"]), 1), r(100 * float(v["sep_nov_2008"]), 1), r(100 * float(v["feb_mar_2020"]), 1))
           for k, v in w.items()}
    assert got == {"PUT": (7.2, 13.8, 0.57, -37.1, -27.6, -19.8), "BXM": (6.0, 14.3, 0.48, -40.1, -28.5, -21.3),
                   "SPX": (9.0, 19.7, 0.53, -56.8, -30.1, -19.9)}


def test_exercises():
    assert r(0.2 * math.sqrt(21 / 252) * 0.8 * 100, 1) == 4.6
    assert r(0.16**2 * 1.3, 4) == 0.0333 and r(math.sqrt(0.16**2 * 1.3), 3) == 0.182
    assert r(-7.7 * 0.10 / math.sqrt(12) * 100, 1) == -22.2


def test_premium_share_and_wipeout():
    cfg, S = market()
    imp, starts = implementations()
    from firm_synthvol import bs_price as price
    prem = np.mean([2 * float(price(1.0, 1.0, 21 / 252, atm_iv(S["v"][t], cfg, 21 / 252), "C")) for t in starts])
    assert (r(100 * prem, 1), r(imp["hedged straddle"].mean() / prem, 3)) == (4.2, 0.128)
    x = imp["short variance"]
    w = x.min() / x.std(ddof=1)
    assert (r(w), r(1 / (abs(w) / math.sqrt(12)), 2)) == (-7.68, 0.45)
    t = leverage_table((0.3, 0.5))
    assert (r(100 * t[0.3]["worst"], 1), t[0.3]["dead"], r(100 * t[0.5]["worst"], 1), t[0.5]["dead"]) == (-66.5, False, -110.8, True)


def test_crash_years():
    cfg, _ = market()
    assert [r(s / 252, 1) for s, _ in cfg.crashes] == [6.0, 12.7, 17.5]
