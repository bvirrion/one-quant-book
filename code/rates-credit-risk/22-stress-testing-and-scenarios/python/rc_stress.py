"""Chapter 22 of Book 6: stress testing chapter 21's book. Historical scenarios from US Treasury par
yields and ECB reference rates (Lehman, September-October 2008; March 2020; September 2022), a
hypothetical ten-year yield shock completed by conditioning, reverse stress tests (linear and full
revaluation) against the ten-day covariance, and, for the weekend problem, a prime broker's total return
swap book on five concentrated stocks (illustrative) and the move that exhausts its margin."""
import csv
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/stresstest", "code/rates-credit-risk/21-market-risk-measures/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_var as rv  # noqa: E402
from firm_stresstest import condition, historical, mahalanobis, reverse_linear, reverse_nonlinear  # noqa: E402

LOG = (2, 3)


def data_2008():
    with open(ROOT / "data/rates-credit-risk/stress_2008.csv") as fh:
        rows = list(csv.DictReader(fh))
    dates = [r["date"] for r in rows]
    lv = np.array([[float(r["y2"]) / 100, float(r["y10"]) / 100, float(r["usd_per_eur"]),
                    float(r["jpy_per_eur"]) / float(r["usd_per_eur"])] for r in rows])
    return dates, lv


def scenarios():
    d08, l08 = data_2008()
    d, lv = rv.data()
    return [historical("Lehman 2008", d08, l08, "2008-09-12", "2008-10-10", LOG),
            historical("March 2020", d, lv, "2020-03-06", "2020-03-20", LOG),
            historical("September 2022", d, lv, "2022-09-21", "2022-09-28", LOG)]


_BOOK: list = []


def book():
    if not _BOOK:
        _BOOK.append(rv.today()[3])
    return _BOOK[0]


def pnl(x) -> float:
    return float(book().pnl(np.asarray(x)[None, :])[0])


def cov10(start: str = "2020-01-01") -> np.ndarray:
    """Ten-day covariance: 10 x the covariance of daily moves since `start` (full sample, equal weights)."""
    d, lv = rv.data()
    x = rv.changes(lv)
    k = next(i for i, s in enumerate(d[1:]) if s >= start)
    return 10 * np.cov(x[k:].T, bias=True)


def historical_table():
    b = book()
    return [(s.name, s.moves, float(b.pnl(s.moves[None, :])[0])) for s in scenarios()]


def var10() -> float:
    return rv.measures()["hs"][0][0] * math.sqrt(10)


def hypothetical(shock_bp: float = 100.0) -> dict:
    """Ten-year yield up shock_bp; the other factors by conditioning on the ten-day covariance."""
    c = cov10()
    x = condition(c, [1], [shock_bp * 1e-4])
    alone = np.zeros(4)
    alone[1] = shock_bp * 1e-4
    return {"x": x, "pnl": pnl(x), "alone": pnl(alone), "distance": mahalanobis(x, c)}


def reverse(loss: float = 10e6) -> dict:
    c = cov10()
    d, _ = book().greeks()
    xl, dl = reverse_linear(d, c, loss)
    xn, dn = reverse_nonlinear(pnl, c, loss, xl)
    return {"x_lin": xl, "d_lin": dl, "pnl_lin_full": pnl(xl), "x_nl": xn, "d_nl": dn, "pnl_nl": pnl(xn)}


# ---- weekend problem: a prime broker's swap book ------------------------------------------------------
NOTIONAL = 20e9
WEIGHTS = np.array([0.30, 0.25, 0.20, 0.15, 0.10])
BETA, MKT_VOL, IDIO_VOL = 1.2, 0.012, 0.030          # daily, illustrative
MARGIN_RATE, HORIZON = 0.075, 5                       # margin as a share of notional; days to liquidate


def stock_cov(days: int = HORIZON) -> np.ndarray:
    b = np.full(5, BETA)
    return days * (np.outer(b, b) * MKT_VOL ** 2 + np.diag(np.full(5, IDIO_VOL ** 2)))


def broker_loss_move(margin_rate: float = MARGIN_RATE) -> dict:
    """If the client defaults, the broker holds the hedge stocks; the most plausible joint fall that
    consumes the margin, over the liquidation horizon."""
    delta = NOTIONAL * WEIGHTS                          # broker long the stocks after the client's default
    c = stock_cov()
    x, dist = reverse_linear(delta, c, margin_rate * NOTIONAL)
    sd = math.sqrt(delta @ c @ delta)
    from statistics import NormalDist
    return {"margin": margin_rate * NOTIONAL, "x": x, "distance": dist, "sd": sd,
            "prob": NormalDist().cdf(-dist), "uniform_fall": margin_rate}


def reverse_without_straddle(loss: float = 10e6) -> dict:
    old = rv.STRADDLE
    rv.STRADDLE = 0.0
    try:
        b = rv.Book(rv.data()[1][-1])
        d, _ = b.greeks()
        c = cov10()
        x, dist = reverse_linear(d, c, loss)
        xn, dn = reverse_nonlinear(lambda z: float(b.pnl(np.asarray(z)[None, :])[0]), c, loss, x)
    finally:
        rv.STRADDLE = old
    return {"d_lin": dist, "d_nl": dn}
