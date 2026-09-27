"""Numbers gate: every numerical answer printed in Book 12, chapter 4 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_baselines as b  # noqa: E402


def pct(x, d=2):
    return round(100 * float(x), d)


def row(v):
    return (pct(v["r2"]), round(v["ic"], 3), round(v["ic_t"], 1), round(v["ls_sr"], 2), round(v["ls_sr_net"], 2),
            round(v["turnover"], 2))


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_table():
    rows, chosen = b.table()
    assert chosen == {"ridge": 1e4, "lasso": 1e-3, "elastic net": 1e-3, "PCR": 10, "PLS": 1, "ridge on splines": 1e4}
    assert pct(rows["ceiling"]["r2"]) == 0.71
    assert row(rows["OLS"]) == (0.25, 0.060, 5.6, 1.85, 1.61, 0.83)
    assert row(rows["ridge"]) == (0.30, 0.060, 5.6, 1.83, 1.59, 0.83)
    assert row(rows["lasso"]) == (0.32, 0.066, 6.7, 2.17, 1.91, 0.80) == row(rows["elastic net"])
    assert row(rows["PCR"]) == (0.13, 0.043, 4.1, 1.23, 0.99, 0.77)
    assert row(rows["PLS"]) == (0.25, 0.061, 5.6, 1.87, 1.62, 0.82)
    assert row(rows["logistic"]) == (0.22, 0.060, 5.7, 1.84, 1.59, 0.84)
    assert row(rows["ridge on splines"]) == (0.35, 0.064, 6.2, 1.98, 1.69, 0.95)
    assert row(rows["boosted trees"]) == (0.47, 0.076, 7.8, 2.20, 1.90, 0.97)
    assert rows["lasso"]["nonzero"] == 6


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_paths_and_crossing():
    p = b.paths()
    assert abs(p["lasso"][1][-1]) < 1e-6 and max(p["ridge"][1]) == p["ridge"][1][2]
    c = {m: (pct(rg), pct(gb), round(rs, 2), round(gs, 2)) for m, rg, gb, rs, gs, _ in b.crossing()}
    assert c[24] == (0.16, -0.71, 0.90, 1.11) and c[60][:2] == (0.18, -0.02) and c[120][:2] == (0.34, 0.41)
    m, s = b.net_difference()
    assert (pct(m), pct(s)) == (-0.08, 2.56) and (2 * 2.56 / 0.08) ** 2 > 4000


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    assert (round(2.4 * 20 / 100, 2), round(2.4 / 2, 1)) == (0.48, 1.2)
    assert (round(1.6 / 2.5 * math.sqrt(12), 2), round(1.4 / 2.5 * math.sqrt(12), 2)) == (2.22, 1.94)
    r0, _ = b.table(style=0.0)
    assert (round(r0["ridge"]["ls_sr_net"], 2), round(r0["boosted trees"]["ls_sr_net"], 2),
            round(r0["lasso"]["ls_sr_net"], 2)) == (3.68, 4.86, 4.24)
    assert (pct(r0["ridge"]["r2"]), pct(r0["boosted trees"]["r2"])) == (0.35, 0.57)
    assert round(r0["boosted trees"]["ls_sr"], 1) == 5.7


def test_small_runs():
    # A 100-name, 10-feature panel instead of the table's cross-validation: ridge shrinks the coefficients as its
    # penalty grows, and the lasso sets some exactly to zero.
    import numpy as np

    P = b.data(n=100, k=10)
    X, y = P.X.reshape(-1, P.X.shape[-1]), (P.r - P.r.mean(axis=1, keepdims=True)).reshape(-1)
    norms = [float(np.linalg.norm(b.ridge(a).fit(X, y).coef_)) for a in (1.0, 1e3, 1e6)]
    assert norms[0] > norms[1] > norms[2] > 0
    assert (b.lasso(1e-3).fit(X, y).coef_ == 0).any()
