"""Numbers gate: every numerical answer printed in Book 7, chapter 24 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rs_riskmodel as rm
from rs_riskmodel import (
    WARM,
    YEAR,
    books,
    decomposition,
    fit_r2,
    forecast,
    fundamental,
    market_bias,
    random_bias,
    rms_exposure,
    specific_deciles,
    summary,
)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "riskmodel"))
import numpy as np  # noqa: E402
from firm_riskmodel import bias_band  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exposed_book_and_models():
    s = summary()
    assert [tuple(r(v, k) for v, k in zip(s[m], (4, 4, 2), strict=True)) for m in ("full", "no momentum", "statistical")] == \
        [(0.0923, 0.092, 1.04), (0.0326, 0.092, 2.86), (0.0559, 0.092, 1.68)]
    assert r(s["no momentum"][1] / s["no momentum"][0]) == 2.83
    s3 = summary(0.3)
    assert (r(s3["no momentum"][2]), r(s3["full"][2]), r(s3["statistical"][2]), r(100 * s3["full"][1]), r(100 * s3["no momentum"][0])) == \
        (1.98, 1.02, 1.48, 6.53, 3.34)
    d = decomposition()
    assert (r(100 * d["vol"]), r(100 * d["factor"], 0), r(100 * d["momentum"], 0), r(d["exposure"])) == (6.88, 76, 76, 1.03)
    assert r(rms_exposure()) == 1.23
    F = fundamental()["F"][WARM:]
    vol = F.std(axis=0) * math.sqrt(YEAR)
    assert (r(100 * vol[0], 1), r(100 * vol[-1], 1), r(100 * vol[1:11].min(), 1), r(100 * vol[1:11].max(), 1)) == \
        (17.8, 7.2, 8.0, 8.7)
    assert r(fit_r2()) == 0.19


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_calibration():
    n = len(forecast(books()[0]["exposed"], fundamental())[0])
    lo, hi = bias_band(n)
    assert (n, r(hi - 1, 3), r(bias_band(252)[1] - 1, 3)) == (2016, 0.031, 0.089)
    rb, rb0 = random_bias(), random_bias(False)
    inside = lambda b: r(100 * np.mean((b > lo) & (b < hi)), 0)  # noqa: E731
    assert (r(rb.mean()), inside(rb), r(rb0.mean()), inside(rb0), r(rb.min()), r(rb.max())) == \
        (1.00, 92, 1.00, 98, 0.96, 1.04)
    mb = market_bias()
    assert (r(mb[False][0]), r(mb[True][0])) == (1.00, 0.99)
    assert (r(mb[False][1].min()), r(mb[False][1].max()), r(mb[True][1].min()), r(mb[True][1].max())) == \
        (0.50, 1.55, 0.56, 1.32)
    out = [r(100 * np.mean(np.abs(mb[a][1] - 1) > math.sqrt(2 / 252)), 0) for a in (False, True)]
    assert out == [66, 44]
    sd = specific_deciles()
    assert (r(sd["spec_raw"][0]), r(sd["spec_raw"][-1])) == (1.13, 0.93)
    assert (r(max(sd["spec"])), r(min(sd["spec"]))) == (1.04, 0.97)


def test_exercises():
    assert r(math.sqrt(3.26**2 + (1.23 * 7.2) ** 2), 1) == 9.4 and r(9.4 / 3.26, 1) == 2.9
    assert r(math.sqrt(2 / 60), 2) == 0.18 and r(math.sqrt(2 / 2016), 3) == 0.031 and r(math.sqrt(0.75), 3) == 0.866


def test_small_runs():
    # The chapter's book-building steps on a small random cross-section (the synthetic market is the reference run):
    # a long-short book is dollar-neutral, and neutralising it leaves no exposure to the factors, at gross 2.
    rng = np.random.default_rng(0)
    listed = rng.random(200) > 0.1
    X = rng.standard_normal((200, 4))
    w = rm._long_short(rng.standard_normal(200), listed, 20)
    assert abs(w.sum()) < 1e-12 and (w > 0).sum() == (w < 0).sum() == 20
    n = rm._neutral(w, X, listed)
    assert np.abs(X[listed].T @ n[listed]).max() < 1e-9 and abs(np.abs(n).sum() - 2.0) < 1e-9 and (n[~listed] == 0).all()
    z = rm._z(rng.standard_normal(200), listed, rng.random(200))
    assert abs(np.std(z[listed]) - 1) < 1e-9 and (z[~listed] == 0).all()
