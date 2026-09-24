"""Chapter 3 of Book 6: rates risk. A 200-swap book on an eight-pillar SOFR curve: its par and
zero ladders and the Jacobian between them, key-rate ladders, principal components of daily US
Treasury par-yield changes (2016-2026), the minimum-variance hedge with three swaps, the P&L of
21 October 2022, and cross-gamma."""
import datetime as dt
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ratesrisk"))
sys.path.insert(0, str(ROOT / "code/firm/curvebuild"))
from firm_curvebuild import Swap, calibrate, swap_pv, with_quote  # noqa: E402
from firm_ratesrisk import (  # noqa: E402
    cross_gamma,
    key_rate_ladder,
    min_variance_hedge,
    par_ladder,
    par_to_zero,
    pca,
    zero_ladder,
)

SPOT = dt.date(2026, 9, 29)
TENORS = [1, 2, 3, 5, 7, 10, 20, 30]
RATES = [0.0360, 0.0340, 0.0335, 0.0343, 0.0357, 0.0375, 0.0405, 0.0403]    # illustrative SOFR swaps
KIND = "flat_forward"
DATA = ROOT / "data/rates-credit-risk/treasury_par_yields.csv"
COLS = ["y1", "y2", "y3", "y5", "y7", "y10", "y20", "y30"]


def instruments(rates=RATES):
    return [Swap(SPOT, n, r, f"{n}Y") for n, r in zip(TENORS, rates, strict=True)]


def curve():
    return calibrate(SPOT, instruments(), KIND)


def random_book(n: int = 200, seed: int = 6):
    """(years, notional, fixed, payer) for n swaps, then two balancing swaps (2Y payer and 30Y
    receiver sized so that the book has zero parallel DV01 and loses on a steepening)."""
    rng = np.random.default_rng(seed)
    c = curve().curve
    book = []
    for _ in range(n):
        yrs = int(rng.integers(1, 31))
        q = float(np.round(np.exp(rng.normal(np.log(40e6), 0.7)), -5))
        par = Swap(SPOT, yrs, 0.0).model(c)
        book.append((yrs, q, round(par + float(rng.normal(0, 0.004)), 5), bool(rng.random() < 0.5)))
    return book


def book_pv(book):
    return lambda cv: sum(swap_pv(cv, SPOT, y, k, q, p) for y, q, k, p in book)


def balanced_book(target_loss: float = -3.0e6, move=None):
    """Add a 2Y payer and a 30Y receiver (at par) so that the parallel DV01 is zero and the
    first-order P&L under `move` (bp per pillar) equals target_loss."""
    move = MOVE_2022_10_21 if move is None else move
    base = random_book()
    g0 = par_ladder(SPOT, instruments(), KIND, book_pv(base))
    c = curve().curve
    unit = {n: par_ladder(SPOT, instruments(), KIND, book_pv([(n, 1e8, Swap(SPOT, n, 0.0).model(c), True)]))
            for n in (2, 30)}
    a = np.array([[unit[2].sum(), unit[30].sum()], [unit[2] @ move, unit[30] @ move]])
    b = np.array([-g0.sum(), target_loss - g0 @ move])
    x = np.linalg.solve(a, b)          # in units of 100 million payer swaps
    extra = [(n, abs(x[i]) * 1e8, Swap(SPOT, n, 0.0).model(c), bool(x[i] > 0)) for i, n in enumerate((2, 30))]
    return base + extra, extra


# ---- data --------------------------------------------------------------------------------------------
def treasury_changes(start: str = "2016-01-01", end: str = "2026-12-31") -> tuple[list[str], np.ndarray]:
    rows = [ln.strip().split(",") for ln in open(DATA) if ln[0].isdigit()]
    rows = [r for r in rows if start <= r[0] <= end]
    levels = np.array([[float(x) for x in r[1:]] for r in rows])
    return [r[0] for r in rows[1:]], np.diff(levels, axis=0) * 100.0      # basis points


def move_on(day: str) -> np.ndarray:
    dates, ch = treasury_changes()
    return ch[dates.index(day)]


MOVE_2022_10_21 = np.array([-8.0, -13.0, -14.0, -11.0, -8.0, -3.0, 7.0, 9.0])


def components():
    _, ch = treasury_changes()
    return pca(ch)


def hedge(book, cols=(1, 6, 7)):
    """Minimum-variance hedge of the book's par ladder with par swaps at the given pillars
    (2Y, 20Y, 30Y by default), using the covariance of daily Treasury par changes as the move model."""
    g = par_ladder(SPOT, instruments(), KIND, book_pv(book))
    c = curve().curve
    hl = np.column_stack([par_ladder(SPOT, instruments(), KIND,
                                     book_pv([(TENORS[k], 1e8, Swap(SPOT, TENORS[k], 0.0).model(c), True)]))
                          for k in cols])
    _, ch = treasury_changes()
    cov = np.cov(ch.T)
    h, share = min_variance_hedge(g, hl, cov)
    return {"ladder": g, "hedge_ladders": hl, "units": h, "residual_share": share, "cov": cov,
            "daily_sd": float(np.sqrt(g @ cov @ g)), "hedged": g + hl @ h}


def full_revaluation(book, move) -> float:
    """P&L when every par quote moves by `move` (bp): recalibrate and reprice."""
    ins = instruments()
    moved = [with_quote(i, i.quote() + m * 1e-4) for i, m in zip(ins, move, strict=True)]
    pv = book_pv(book)
    return pv(calibrate(SPOT, moved, KIND).curve) - pv(calibrate(SPOT, ins, KIND).curve)


def zero_and_key_ladders(book):
    cal = curve()
    pv = book_pv(book)
    return {"zero": zero_ladder(cal.curve, pv), "jacobian": cal.jacobian,
            "par": par_ladder(SPOT, instruments(), KIND, pv),
            "key": key_rate_ladder(cal.curve, [cal.curve.t(Swap(SPOT, n, 0).maturity) for n in TENORS], pv),
            "par_to_zero": par_to_zero(par_ladder(SPOT, instruments(), KIND, pv), cal.jacobian)}


def gamma_matrix(book):
    return cross_gamma(SPOT, instruments(), KIND, book_pv(book))
