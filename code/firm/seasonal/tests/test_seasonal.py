import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_seasonal import calendar, profile, rules, same_month, score_rules  # noqa: E402


def test_calendar_and_rules():
    c = calendar(2)
    assert len(c["dom"]) == 504 and c["dom"][21] == 0 and c["moy"][21] == 1 and c["year"][252] == 1
    assert c["post"].sum() == 18 and c["pre"].sum() == 17            # no day before the first holiday of the sample
    R = rules(c)
    assert len(R) == 100 and len({n for n, _ in R}) == 100


def test_rule_scores_find_a_planted_day():
    c = calendar(20)
    r = np.random.default_rng(0).normal(0, 0.01, len(c["dom"]))
    r[c["dom"] == 0] += 0.004
    names, t, p = score_rules(r, rules(c))
    i = names.index("day 1 of month")
    assert t[i] > 5 and p[i] < 1e-6 and math.isclose(p[i], math.erfc(t[i] / math.sqrt(2)))


def test_profile_and_same_month():
    assert np.allclose(profile(np.arange(12.0), 4), [4, 5, 6, 7])
    M = np.zeros((36, 2))
    M[::12, 0] = 1.0
    s = same_month(M, (1, 2))
    assert s[24, 0] == 1.0 and s[25, 0] == 0.0 and np.isnan(s[5, 0])
