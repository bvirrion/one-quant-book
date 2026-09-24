"""Multi-instrument curve builder (build of One Quant Book 6, chapter 1).

Extends Book 2's single-curve bootstrap (`firm_curve`, imported, never edited) with:
- three instrument types quoted as rates: overnight deposits (one period), three-month
  overnight-rate futures (price and convexity adjustment) and annual OIS swaps;
- four interpolations of the continuously compounded zero rate z(t), pillar by pillar:
  "linear_zero", "flat_forward" (log discount factor linear), "cubic_zero" (natural cubic
  spline) and "monotone_convex" (Hagan and West 2006, on the discrete forwards);
- a global Newton calibration of all pillar zero rates at once (every interpolation, local or
  not), which also returns the Jacobian of the model quotes with respect to the pillars;
- bucketed sensitivities by bump-and-recalibrate.

Pillars are the instruments' maturities, in increasing order. Times are ACT/365 from the spot
date; accruals ACT/360; no business-day adjustment (as in Book 2's teaching curve).
"""
import datetime as dt
import math
import pathlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "curve"))
from firm_curve import add_years, annuity, schedule  # noqa: E402

KINDS = ("linear_zero", "flat_forward", "cubic_zero", "monotone_convex")


# ---- instruments ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class Deposit:
    """One-period overnight-index deposit (an OIS with a single payment): simple rate, ACT/360."""
    start: dt.date
    end: dt.date
    rate: float
    label: str = ""

    @property
    def maturity(self) -> dt.date:
        return self.end

    def quote(self) -> float:
        return self.rate

    def model(self, curve) -> float:
        return (curve.df(self.start) / curve.df(self.end) - 1) / ((self.end - self.start).days / 360)


@dataclass(frozen=True)
class Future:
    """Three-month overnight-rate future: price 100 minus the compounded rate of its reference
    quarter. The curve must match the futures rate minus the convexity adjustment."""
    start: dt.date
    end: dt.date
    price: float
    convexity: float = 0.0
    label: str = ""

    @property
    def maturity(self) -> dt.date:
        return self.end

    def quote(self) -> float:
        return (100.0 - self.price) / 100.0 - self.convexity

    def model(self, curve) -> float:
        return (curve.df(self.start) / curve.df(self.end) - 1) / ((self.end - self.start).days / 360)


@dataclass(frozen=True)
class Swap:
    """Par OIS swap, annual on both legs, ACT/360, single curve."""
    start: dt.date
    years: int
    rate: float
    label: str = ""

    @property
    def maturity(self) -> dt.date:
        return add_years(self.start, self.years)

    def quote(self) -> float:
        return self.rate

    def model(self, curve) -> float:
        dates = schedule(self.start, self.years)
        return (curve.df(dates[0]) - curve.df(dates[-1])) / annuity(curve, dates)


def with_quote(inst, q: float):
    """The same instrument with its rate quote replaced by q (for futures: the adjusted rate)."""
    if isinstance(inst, Future):
        return Future(inst.start, inst.end, 100.0 * (1.0 - q - inst.convexity), inst.convexity, inst.label)
    if isinstance(inst, Deposit):
        return Deposit(inst.start, inst.end, q, inst.label)
    return Swap(inst.start, inst.years, q, inst.label)


# ---- interpolation of z(t) -------------------------------------------------------------------------
def _natural_cubic(xs: Sequence[float], ys: Sequence[float]) -> Callable[[float], float]:
    """Natural cubic spline through (xs, ys); second derivatives by the tridiagonal system."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    a = np.zeros((n, n))
    b = np.zeros(n)
    a[0, 0] = a[-1, -1] = 1.0
    for i in range(1, n - 1):
        a[i, i - 1], a[i, i], a[i, i + 1] = h[i - 1], 2 * (h[i - 1] + h[i]), h[i]
        b[i] = 6 * ((ys[i + 1] - ys[i]) / h[i] - (ys[i] - ys[i - 1]) / h[i - 1])
    m = np.linalg.solve(a, b)

    def s(x: float) -> float:
        k = max(1, min(n - 1, int(np.searchsorted(xs, x))))
        x0, x1, hk = xs[k - 1], xs[k], h[k - 1]
        u, v = x1 - x, x - x0
        return (m[k - 1] * u**3 + m[k] * v**3) / (6 * hk) + (ys[k - 1] / hk - m[k - 1] * hk / 6) * u + (
            ys[k] / hk - m[k] * hk / 6) * v
    return s


def _mc_piece(g0: float, g1: float) -> list[tuple[float, float, Callable[[float], float]]]:
    """Hagan-West function G(x) on [0,1] (forward minus discrete forward), as pieces (a, b, G)."""
    if g0 == 0.0 and g1 == 0.0:
        return [(0.0, 1.0, lambda x: 0.0)]
    if (g0 < 0 and -0.5 * g0 <= g1 <= -2 * g0) or (g0 > 0 and -0.5 * g0 >= g1 >= -2 * g0):   # region (i)
        return [(0.0, 1.0, lambda x: g0 * (1 - 4 * x + 3 * x * x) + g1 * (-2 * x + 3 * x * x))]
    if (g0 < 0 and g1 > -2 * g0) or (g0 > 0 and g1 < -2 * g0):                                 # region (ii)
        eta = (g1 + 2 * g0) / (g1 - g0)
        return [(0.0, eta, lambda x: g0), (eta, 1.0, lambda x: g0 + (g1 - g0) * ((x - eta) / (1 - eta)) ** 2)]
    if (g0 > 0 and 0 > g1 > -0.5 * g0) or (g0 < 0 and 0 < g1 < -0.5 * g0):                     # region (iii)
        eta = 3 * g1 / (g1 - g0)
        return [(0.0, eta, lambda x: g1 + (g0 - g1) * ((eta - x) / eta) ** 2), (eta, 1.0, lambda x: g1)]
    eta = g1 / (g1 + g0)                                                                        # region (iv)
    amp = -g0 * g1 / (g0 + g1)
    return [(0.0, eta, lambda x: amp + (g0 - amp) * ((eta - x) / eta) ** 2),
            (eta, 1.0, lambda x: amp + (g1 - amp) * ((x - eta) / (1 - eta)) ** 2)]


def _integral(pieces, x: float) -> float:
    """Integral of the piecewise quadratic G from 0 to x (Simpson's rule is exact on quadratics)."""
    tot = 0.0
    for a, b, g in pieces:
        if x <= a:
            break
        c = min(x, b)
        if c > a:
            tot += (c - a) / 6 * (g(a) + 4 * g((a + c) / 2) + g(c))
    return tot


class _MonotoneConvex:
    """Hagan-West monotone convex interpolation of y(t) = z(t) t, from (0, 0) through the pillars."""

    def __init__(self, ts: Sequence[float], zs: Sequence[float]):
        self.t = [0.0] + list(ts)
        y = [0.0] + [z * t for z, t in zip(zs, ts, strict=True)]
        n = len(ts)
        self.fd = [0.0] + [(y[i] - y[i - 1]) / (self.t[i] - self.t[i - 1]) for i in range(1, n + 1)]
        f = [0.0] * (n + 1)
        for i in range(1, n):
            t0, t1, t2 = self.t[i - 1], self.t[i], self.t[i + 1]
            f[i] = (t1 - t0) / (t2 - t0) * self.fd[i + 1] + (t2 - t1) / (t2 - t0) * self.fd[i]
        f[0] = self.fd[1] - 0.5 * (f[1] - self.fd[1]) if n > 1 else self.fd[1]
        f[n] = self.fd[n] - 0.5 * (f[n - 1] - self.fd[n]) if n > 1 else self.fd[n]
        self.f = f
        self.y = y
        self.pieces = [None] + [_mc_piece(f[i - 1] - self.fd[i], f[i] - self.fd[i]) for i in range(1, n + 1)]

    def _seg(self, t: float) -> tuple[int, float]:
        i = max(1, min(len(self.t) - 1, int(np.searchsorted(self.t, t))))
        return i, (t - self.t[i - 1]) / (self.t[i] - self.t[i - 1])

    def yint(self, t: float) -> float:
        i, x = self._seg(t)
        h = self.t[i] - self.t[i - 1]
        return self.y[i - 1] + self.fd[i] * (t - self.t[i - 1]) + h * _integral(self.pieces[i], x)

    def fwd(self, t: float) -> float:
        i, x = self._seg(t)
        g = next(gg for a, b, gg in self.pieces[i] if x <= b)
        return self.fd[i] + g(x)


class ZeroCurve:
    """Discount curve z(t) interpolated between pillar zero rates; conforms to the pricing library's
    DiscountCurve / BumpableCurve protocols (One Quant Book 5, chapter 28)."""

    def __init__(self, spot: dt.date, times: Sequence[float], zeros: Sequence[float], kind: str = "flat_forward",
                 labels: Sequence[str] | None = None):
        if kind not in KINDS:
            raise ValueError(kind)
        self.spot, self.times, self.zeros, self.kind = spot, list(times), list(zeros), kind
        self.labels = list(labels) if labels else [f"P{i}" for i in range(len(times))]
        ts, zs = self.times, self.zeros
        if kind == "monotone_convex":
            self._mc = _MonotoneConvex(ts, zs)
        elif kind == "cubic_zero":
            self._sp = _natural_cubic(ts, zs)
        self._last_fwd = (zs[-1] * ts[-1] - zs[-2] * ts[-2]) / (ts[-1] - ts[-2]) if len(ts) > 1 else zs[0]

    def t(self, d: dt.date) -> float:
        return (d - self.spot).days / 365.0

    def yint(self, t: float) -> float:
        """Integral of the instantaneous forward from 0 to t, i.e. z(t) t = -ln P(t)."""
        ts, zs = self.times, self.zeros
        if t <= 0:
            return 0.0
        if t >= ts[-1]:
            return zs[-1] * ts[-1] + self._last_fwd * (t - ts[-1])
        if self.kind == "monotone_convex":
            return self._mc.yint(t)
        if t <= ts[0]:
            return zs[0] * t
        if self.kind == "cubic_zero":
            return self._sp(t) * t
        k = int(np.searchsorted(ts, t))
        w = (t - ts[k - 1]) / (ts[k] - ts[k - 1])
        if self.kind == "linear_zero":
            return (zs[k - 1] + w * (zs[k] - zs[k - 1])) * t
        return zs[k - 1] * ts[k - 1] + w * (zs[k] * ts[k] - zs[k - 1] * ts[k - 1])      # flat forward

    def df_t(self, t: float) -> float:
        return math.exp(-self.yint(t))

    def df(self, d: dt.date) -> float:
        return self.df_t(self.t(d))

    def zero_t(self, t: float) -> float:
        return self.yint(t) / t

    def fwd_t(self, t: float, h: float = 1e-5) -> float:
        """Instantaneous forward rate f(0, t) = d(z t)/dt."""
        if self.kind == "monotone_convex" and 0 < t < self.times[-1]:
            return self._mc.fwd(t)
        return (self.yint(t + h) - self.yint(max(t - h, 0.0))) / (t + h - max(t - h, 0.0))

    def bumped(self, pillar: str | None, size: float) -> "ZeroCurve":
        """New curve with one pillar's zero rate (or all, pillar=None) shifted by size."""
        zs = [z + size if (pillar is None or lab == pillar) else z for z, lab in zip(self.zeros, self.labels,
                                                                                    strict=True)]
        return ZeroCurve(self.spot, self.times, zs, self.kind, self.labels)


# ---- calibration -----------------------------------------------------------------------------------
@dataclass
class Calibration:
    curve: ZeroCurve
    jacobian: np.ndarray        # d(model quote_i) / d(pillar zero_j)
    iterations: int
    max_error: float


def calibrate(spot: dt.date, instruments: Sequence, kind: str = "flat_forward", tol: float = 1e-12,
              max_iter: int = 30) -> Calibration:
    """Solve for every pillar zero rate at once so that each instrument reprices to its quote
    (Newton's method with a finite-difference Jacobian). Pillars = instrument maturities."""
    times = [(i.maturity - spot).days / 365.0 for i in instruments]
    if any(b <= a for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("instrument maturities must be strictly increasing")
    labels = [i.label or f"P{k}" for k, i in enumerate(instruments)]
    quotes = np.array([i.quote() for i in instruments])
    z = quotes.copy()

    def resid(zv):
        c = ZeroCurve(spot, times, list(zv), kind, labels)
        return np.array([i.model(c) for i in instruments]) - quotes

    n, it, r = len(instruments), 0, resid(z)
    jac = np.eye(n)
    while it < max_iter:
        jac = np.empty((n, n))
        for j in range(n):
            e = z.copy()
            e[j] += 1e-7
            jac[:, j] = (resid(e) - r) / 1e-7
        if np.max(np.abs(r)) < tol:
            break
        z = z - np.linalg.solve(jac, r)
        r = resid(z)
        it += 1
    return Calibration(ZeroCurve(spot, times, list(z), kind, labels), jac, it, float(np.max(np.abs(r))))


def swap_pv(curve, start: dt.date, years: int, fixed: float, notional: float, payer: bool = True) -> float:
    """Value of a single-curve OIS to the payer of fixed (or the receiver)."""
    dates = schedule(start, years)
    v = notional * (curve.df(dates[0]) - curve.df(dates[-1]) - fixed * annuity(curve, dates))
    return v if payer else -v


def bucket_sensitivities(spot: dt.date, instruments: Sequence, kind: str, pv: Callable[[ZeroCurve], float],
                         bump: float = 1e-4) -> list[float]:
    """Change in pv when each quote rises by `bump` and the curve is recalibrated."""
    base = pv(calibrate(spot, instruments, kind).curve)
    out = []
    for k, inst in enumerate(instruments):
        shifted = list(instruments)
        shifted[k] = with_quote(inst, inst.quote() + bump)
        out.append(pv(calibrate(spot, shifted, kind).curve) - base)
    return out


def imm_date(year: int, month: int) -> dt.date:
    """Third Wednesday of the month."""
    d = dt.date(year, month, 1)
    return d + dt.timedelta(days=(2 - d.weekday()) % 7 + 14)
