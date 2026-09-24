"""Inflation options in a Jarrow-Yildirim model with deterministic nominal rates (build of One Quant
Book 6, chapter 11).

The foreign-currency analogy: nominal money is the domestic currency, real (index-linked) money the
foreign one, and the price index I(t) the exchange rate. Nominal rates are deterministic here, which
isolates the two effects that matter for year-on-year products: the real rate is Hull-White,
  r_R = f_R(0, t) + x,  dx = (y(t) - kappa x - rho sigma_R sigma_I) dt + sigma_R dW_R   (nominal measure),
and dI / I = (n_t - r_R,t) dt + sigma_I dW_I with d<W_R, W_I> = rho dt.
Year-on-year forwards carry a convexity adjustment; year-on-year caplets are Black on a lognormal
ratio; limited price indexation (capped and floored annual uprating, compounded) is priced by
simulation. Book 2's `firm_breakeven` gives seasonal factors (imported, not edited).
"""
import math
from dataclasses import dataclass

import numpy as np


def _cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def _B(k: float, tau: float) -> float:
    return (1 - math.exp(-k * tau)) / k


class LogLinearCurve:
    """Discount factors from pillar values, log-linear in time (flat forward), P(0) = 1."""

    def __init__(self, times, dfs):
        self.t = np.concatenate([[0.0], np.asarray(times, float)])
        self.l = np.concatenate([[0.0], np.log(np.asarray(dfs, float))])

    def df_t(self, t: float) -> float:
        if t >= self.t[-1]:
            slope = (self.l[-1] - self.l[-2]) / (self.t[-1] - self.t[-2])
            return math.exp(self.l[-1] + slope * (t - self.t[-1]))
        return math.exp(float(np.interp(t, self.t, self.l)))


def real_curve(nominal, years, zc_rates) -> LogLinearCurve:
    """P_R(0, T) = P_N(0, T) (1 + k_T)^T from zero-coupon inflation swap rates k_T."""
    return LogLinearCurve(years, [nominal.df_t(t) * (1 + k) ** t for t, k in zip(years, zc_rates, strict=True)])


@dataclass
class JYDet:
    nominal: object
    real: object
    kappa: float
    sigma_r: float
    sigma_i: float
    rho: float

    def y(self, t: float) -> float:
        return self.sigma_r**2 * (1 - math.exp(-2 * self.kappa * t)) / (2 * self.kappa)

    def mu(self, t: float) -> float:
        """E[x_t] under the real risk-neutral measure: int_0^t exp(-kappa (t - u)) y(u) du."""
        k, s = self.kappa, self.sigma_r
        return s * s / (2 * k * k) * (1 - math.exp(-k * t)) ** 2

    def yoy_ratio(self, T: float, S: float) -> float:
        """E^N[I(S) / I(T)]: the forward ratio times exp(C), C the year-on-year convexity adjustment."""
        fwd = (self.real.df_t(S) / self.real.df_t(T)) / (self.nominal.df_t(S) / self.nominal.df_t(T))
        return fwd * math.exp(self.convexity(T, S))

    def convexity(self, T: float, S: float) -> float:
        b = _B(self.kappa, S - T)
        return -b * (self.mu(T) - self.rho * self.sigma_r * self.sigma_i * _B(self.kappa, T))

    def yoy_log_variance(self, T: float, S: float) -> float:
        k, sr, si, d = self.kappa, self.sigma_r, self.sigma_i, S - T
        before = sr * sr * _B(k, d) ** 2 * (1 - math.exp(-2 * k * T)) / (2 * k)
        during = sr * sr * (d - 2 * _B(k, d) + (1 - math.exp(-2 * k * d)) / (2 * k)) / (k * k)
        int_b = (d - _B(k, d)) / k
        return si * si * d + before + during - 2 * self.rho * si * sr * int_b

    def yoy_caplet(self, T: float, S: float, K: float, floor: bool = False) -> float:
        """Pays max(I(S)/I(T) - 1 - K, 0) at S (or the floorlet)."""
        f, kk, v = self.yoy_ratio(T, S), 1 + K, math.sqrt(self.yoy_log_variance(T, S))
        d1 = math.log(f / kk) / v + 0.5 * v
        call = f * _cdf(d1) - kk * _cdf(d1 - v)
        return self.nominal.df_t(S) * (call if not floor else call - (f - kk))

    def yoy_swap_rate(self, years: int) -> float:
        """Par fixed rate of a year-on-year swap (annual, unit accruals)."""
        leg = sum(self.nominal.df_t(i) * (self.yoy_ratio(i - 1, i) - 1) for i in range(1, years + 1))
        return leg / sum(self.nominal.df_t(i) for i in range(1, years + 1))

    def zc_swap_rate(self, T: float) -> float:
        return (self.real.df_t(T) / self.nominal.df_t(T)) ** (1 / T) - 1

    def simulate_ratios(self, years: int, paths: int, steps: int = 52, seed: int = 11) -> np.ndarray:
        """Annual index ratios I(i)/I(i-1), i = 1..years, under the nominal measure (paths x years)."""
        rng = np.random.default_rng(seed)
        dt = 1.0 / steps
        x = np.zeros(paths)
        ln_i = np.zeros(paths)
        out = np.empty((paths, years))
        prev = np.zeros(paths)
        c = math.sqrt(1 - self.rho**2)
        for k in range(years * steps):
            t = k * dt
            n = -math.log(self.nominal.df_t(t + dt) / self.nominal.df_t(t)) / dt
            fr = -math.log(self.real.df_t(t + dt) / self.real.df_t(t)) / dt
            z1 = rng.standard_normal(paths)
            z2 = self.rho * z1 + c * rng.standard_normal(paths)
            rr = fr + x
            ln_i += (n - rr - 0.5 * self.sigma_i**2) * dt + self.sigma_i * math.sqrt(dt) * z2
            x += (self.y(t) - self.kappa * x - self.rho * self.sigma_r * self.sigma_i) * dt \
                + self.sigma_r * math.sqrt(dt) * z1
            if (k + 1) % steps == 0:
                i = (k + 1) // steps - 1
                out[:, i] = np.exp(ln_i - prev)
                prev = ln_i.copy()
        return out

    def lpi_leg(self, years: int, cap: float = 0.05, floor: float = 0.0, paths: int = 40000, seed: int = 11) -> dict:
        """Value at 0 of LPI(years) = prod (1 + min(max(ratio - 1, floor), cap)) paid at `years`,
        and of the uncapped index ratio I(years)/I(0)."""
        r = self.simulate_ratios(years, paths, seed=seed)
        lpi = np.prod(1 + np.clip(r - 1, floor, cap), axis=1)
        full = np.prod(r, axis=1)
        p = self.nominal.df_t(years)
        return {"lpi": p * lpi.mean(), "lpi_se": p * lpi.std(ddof=1) / math.sqrt(paths),
                "uncapped": p * full.mean(), "uncapped_exact": self.real.df_t(years)}
