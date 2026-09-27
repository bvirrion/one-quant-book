"""Numbers gate: every numerical answer printed in Book 10, chapter 8 (text and solutions)."""
import itertools
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_frag import study  # noqa: E402, I001
from firm_consolidated import nbbo_events  # noqa: E402, I001


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_views_and_locks():
    s = study()
    na, a = s["no_arb"]["lc"], s["arb"]["lc"]
    assert (r(100 * na["locked"], 1), r(100 * na["crossed"], 1), r(na["crossed_median_s"], 1)) == (34.4, 10.0, 4.8)
    assert (r(100 * a["locked"], 1), r(100 * a["crossed"], 2), r(1e6 * a["crossed_median_s"], 0)) == (42.6, 0.07, 41.0)
    assert (na["crossed_episodes"], a["crossed_episodes"], r(a["locked_median_s"], 2)) == (69, 565, 0.44)
    assert s["arb_fills"] == 1410
    assert (s["no_arb"]["volume"]["C"], s["arb"]["volume"]["C"]) == (128100, 230900)
    assert [s["no_arb"]["volume"][v] for v in "AB"] == [322700, 218300]
    assert [r(100 * s["at_best"][v]) for v in "ABC"] == [37.74, 29.88, 32.38]


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_consolidated_feed():
    s = study()
    assert r(100 * s["sip_live"], 4) == r(100 * s["sip_offline"], 4) == 0.0098
    assert [r(100 * s["delays"][d], 3) for d in (0.05, 0.5, 1.0, 5.0, 20.0, 100.0)] == \
        [0.002, 0.009, 0.018, 0.084, 0.327, 1.495]
    assert (r(s["price_changes_per_s"]), r(s["nbbo_changes_per_s"], 1)) == (0.44, 8.4)
    assert (r(100 * s["trades_stale"], 1), r(100 * s["trades_stale_bg"], 2)) == (18.5, 0.02)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_information_shares():
    s = study()
    i, c, i20 = s["is"], s["is_close"], s["is_20"]
    assert [r(x) for x in i["is_low"]] == [0.63, 0.19, 0.01] and [r(x) for x in i["is_high"]] == [0.79, 0.34, 0.04]
    assert [r(x) for x in i["component_share"]] == [0.75, 0.44, -0.20]
    assert [r(x) for x in i20["is_low"]] == [0.53, 0.30, 0.0] and [r(x) for x in i20["is_high"]] == [0.69, 0.45, 0.02]
    assert [r(x) for x in c["is_low"]] == [0.23, 0.37, 0.13] and [r(x) for x in c["is_high"]] == [0.44, 0.59, 0.28]


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    top = np.dtype([("t", "f8"), ("bid", "i8"), ("bid_qty", "i8"), ("ask", "i8"), ("ask_qty", "i8")])
    q = {"V1": (1000, 300, 1002, 200), "V2": (1001, 500, 1003, 100), "V3": (1001, 50, 1002, 400),
         "V4": (999, 1000, 1002, 1000)}
    nb = nbbo_events({k: np.array([(0.0, *v)], dtype=top) for k, v in q.items()})
    assert tuple(nb[-1])[1:] == (1001, 500, 1002, 1600)
    # 3: upper bound rate x delay
    assert (r(100 * 500 * 0.001), r(100 * 0.44 * 0.0005, 3)) == (50.0, 0.022)
    # 4: information-share bounds for two venues
    psi, om = np.array([0.6, 0.4]), np.array([[1.0, 0.5], [0.5, 1.0]])
    tot = psi @ om @ psi
    shares = {}
    for perm in itertools.permutations(range(2)):
        idx = list(perm)
        f = np.linalg.cholesky(om[np.ix_(idx, idx)])
        for k, j in enumerate(idx):
            shares.setdefault(j, []).append((psi[idx] @ f)[k] ** 2 / tot)
    assert (r(tot), r(min(shares[0]), 3), r(max(shares[0]), 3), r(min(shares[1]), 3), r(max(shares[1]), 3)) == \
        (0.76, 0.355, 0.842, 0.158, 0.645)
    # 5: component shares from alpha = (-0.2, 0.3)
    a_perp = np.array([0.3, 0.2])
    assert [r(x) for x in a_perp / a_perp.sum()] == [0.6, 0.4]
    assert abs(np.array([-0.2, 0.3]) @ a_perp) < 1e-12


def test_small_runs():
    # Ten minutes of the fragmented market instead of an hour: the consolidated quote moves, the arbitrageur
    # trades, and every venue trades.
    s = study(seconds=600.0)
    assert s["nbbo_changes_per_s"] > 0 and s["arb_fills"] > 0 and {"arb", "no_arb"} <= set(s)
    assert all(v > 0 for v in s["arb"]["volume"].values())
