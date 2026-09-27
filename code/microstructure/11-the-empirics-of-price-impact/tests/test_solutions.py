"""Numbers gate: every numerical answer printed in Book 10, chapter 11 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_impact import counterfactual, panel, panel_fits, replay_pitfall, single_and_aggregate  # noqa: E402, I001
from firm_impactfit import fit_power  # noqa: E402, I001


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_single_and_aggregate():
    s = single_and_aggregate()
    assert (s["volume"], s["trades"]) == (763_900, 7639)
    b = list(s["response"]["by_size"].values())
    assert [r(v[0]) for v in b] == [0.27, 0.58, 1.12, 2.34]
    assert [r(v[-1]) for v in b] == [0.81, 0.23, 0.68, 0.46]
    a = s["aggregate"]
    assert (r(a["slope"] * 1000, 1), a["n"][3]) == (2.1, 163)
    assert [r(x, 1) for x in a["dm"][1:6]] == [-3.1, -1.4, 0.2, 0.7, 3.1]


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_metaorders():
    assert replay_pitfall()["diff"] == [0.0, 0.0, 0.0, 0.0]
    c = counterfactual()
    assert r(c["hourly_volume"], -2) == 749_200
    m, e = c[24000]
    assert ([r(x, 1) for x in m], [r(x, 1) for x in e]) == ([6.3, 7.8, -1.5, 0.8], [1.9, 2.2, 1.5, 2.8])
    assert (r(c[6000][0][1], 1), r(c[6000][1][1], 1), r(c[1500][0][1], 1), r(c[1500][1][1], 1)) == (2.6, 1.9, 2.4, 0.9)
    assert r(100 * 24000 / 749_200, 1) == 3.2


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_panel():
    f = panel_fits()
    c, t, k = f["clean"], f["timed"], f["corrected"]
    assert (r(c["exponent"]), r(c["prefactor"]), r(c["prefactor_sqrt"])) == (0.48, 0.85, 0.81)
    assert ([r(x) for x in c["exponent_ci"]], [r(x) for x in c["prefactor_ci"]]) == ([0.39, 0.56], [0.55, 1.66])
    assert (r(t["exponent"]), r(t["prefactor"]), r(t["prefactor_sqrt"])) == (0.50, 1.42, 1.31)
    assert ([r(x) for x in t["exponent_ci"]], [r(x) for x in t["prefactor_ci"]]) == ([0.44, 0.55], [1.01, 2.04])
    assert (r(k["exponent"]), r(k["prefactor"]), r(f["beta"])) == (0.48, 0.85, 1.54)
    assert r(100 * (t["prefactor_sqrt"] / c["prefactor_sqrt"] - 1), 0) == 62.0
    p = panel(1)
    assert (len(p["impact"]), r(p["participation"].min() * 1e4, 1), r(p["participation"].max() * 100, 1)) == (2000, 1.0, 5.0)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    # 1: square-root law with Y = 0.8, sigma = 2%: 1% and 4% of the daily volume, in basis points
    assert (r(0.8 * 0.02 * 0.01**0.5 * 1e4, 0), r(0.8 * 0.02 * 0.04**0.5 * 1e4, 0)) == (16.0, 32.0)
    # 7: a fixed horizon of a tenth of a day
    a = panel(1, 0.3, dur_fixed=0.1)
    b = panel(1, 0.0, dur_fixed=0.1)
    fa = fit_power(a["impact"], a["sigma"], a["participation"], clusters=a["stock"])
    fb = fit_power(b["impact"], b["sigma"], b["participation"], clusters=b["stock"])
    assert (r(fb["exponent"]), r(fa["exponent"]), r(fb["prefactor_sqrt"]), r(fa["prefactor_sqrt"])) == (0.28, 0.20, 0.81, 1.24)


def test_small_runs():
    # Fifteen minutes of tape and one seed of metaorders instead of the panels: the market trades, and a
    # 24,000-share buy moves the price up, further than a 1,500-share one (same seed, same background flow).
    s = single_and_aggregate(seconds=900.0)
    assert s["trades"] > 0 and s["volume"] > 0 and {"lags", "all", "by_size"} <= set(s["response"])
    c = counterfactual(sizes=(1500, 24_000), seeds=(1,))
    assert c[24_000][0][0] > 0 and c[24_000][0][0] >= c[1500][0][0]
