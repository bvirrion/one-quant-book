"""Convertible bonds (build of Book 5, Chapter 21): a Crank-Nicolson pricer in log-spot with a hazard rate that
may depend on the share price (an equity-to-credit model), discrete coupons, conversion at any time, an issuer
call with a soft-call trigger and an investor put; delta, gamma and credit sensitivity from the grid.

Under the pricing measure the share jumps to zero at default, which arrives with intensity lambda(S); the
bondholder then recovers R times the face. With x = ln S the value V(t, x) solves
    V_t + (1/2) sigma^2 V_xx + (r - q + lambda - sigma^2 / 2) V_x - (r + lambda) V + lambda R F = 0,
subject to V >= conversion value, V <= max(call price, conversion value) when callable, V >= put price when putable.
"""
import math
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Convertible:
    face: float = 100.0
    maturity: float = 5.0
    coupon: float = 0.02                     # annual rate, paid `freq` times a year
    freq: int = 1
    ratio: float = 2.5                       # shares per bond on conversion
    recovery: float = 0.4                    # of face, at default
    call_start: float = 2.0                  # issuer may call from this date ...
    call_price: float = 100.0                # ... at this price ...
    call_trigger: float = 52.0               # ... if the share is at or above this level (soft call)
    puts: tuple[tuple[float, float], ...] = field(default_factory=tuple)   # (date, price) investor puts

    @property
    def conversion_price(self) -> float:
        return self.face / self.ratio


def power_hazard(lam0: float, s0: float, p: float, cap: float = 2.0):
    """lambda(S) = lam0 (S / s0)^(-p), capped: the equity-to-credit link (p = 0 is a constant hazard)."""
    return lambda s: np.minimum(lam0 * (np.asarray(s, float) / s0) ** (-p), cap)


def _tridiag_solve(a, b, c, d):
    """Thomas algorithm for sub-diagonal a, diagonal b, super-diagonal c."""
    n = len(d)
    cp, dp = np.empty(n), np.empty(n)
    cp[0], dp[0] = c[0] / b[0], d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m if i < n - 1 else 0.0
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = np.empty(n)
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


def price_grid(cb: Convertible, r: float, q: float, vol: float, hazard, s_min: float = 0.5, s_max: float = 600.0,
               nx: int = 500, steps_per_year: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Value today on the spot grid (Crank-Nicolson with two implicit Rannacher steps at the start and after each
    coupon). Returns (spots, values)."""
    x = np.linspace(math.log(s_min), math.log(s_max), nx)
    s = np.exp(x)
    dx = x[1] - x[0]
    lam = np.asarray(hazard(s), float)
    conv = cb.ratio * s
    n_steps = round(cb.maturity * steps_per_year)
    dt = cb.maturity / n_steps
    coupon_times = [cb.maturity - k / cb.freq for k in range(round(cb.maturity * cb.freq))]
    coupon_idx = {round(tc / dt) for tc in coupon_times}
    put_idx = {round(tp / dt): pp for tp, pp in cb.puts}
    v = np.maximum(cb.face + cb.face * cb.coupon / cb.freq, conv)            # at maturity: redeem with last coupon
    drift = r - q + lam - 0.5 * vol * vol
    lo = 0.5 * vol * vol / dx ** 2 - 0.5 * drift / dx
    up = 0.5 * vol * vol / dx ** 2 + 0.5 * drift / dx
    mid = -vol * vol / dx ** 2 - (r + lam)
    src = lam * cb.recovery * cb.face
    implicit_left = 2
    for n in range(n_steps, 0, -1):
        theta = 1.0 if implicit_left > 0 else 0.5
        implicit_left -= 1
        rhs = v.copy()
        rhs[1:-1] += (1 - theta) * dt * (lo[1:-1] * v[:-2] + mid[1:-1] * v[1:-1] + up[1:-1] * v[2:]) + dt * src[1:-1]
        a = -theta * dt * lo
        b = 1 - theta * dt * mid
        c = -theta * dt * up
        a[0] = c[0] = 0.0
        b[0] = 1.0
        a[-1] = c[-1] = 0.0
        b[-1] = 1.0
        t_new = (n - 1) * dt
        rhs[0] = cb.recovery * cb.face                                    # deep distress: recovery
        rhs[-1] = conv[-1]                                                # deep in the money: conversion
        v = _tridiag_solve(a, b, c, rhs)
        if (n - 1) in coupon_idx and n - 1 > 0:
            v = v + cb.face * cb.coupon / cb.freq
            implicit_left = 2
        if (n - 1) in put_idx:
            v = np.maximum(v, put_idx[n - 1])
        v = np.maximum(v, conv)                                           # conversion at any time
        if t_new >= cb.call_start - 1e-12:
            callable_ = s >= cb.call_trigger
            v = np.where(callable_, np.minimum(v, np.maximum(cb.call_price, conv)), v)
    return s, v


def value_at(s0: float, grid: tuple[np.ndarray, np.ndarray]) -> float:
    s, v = grid
    return float(np.interp(math.log(s0), np.log(s), v))


def greeks(s0: float, grid: tuple[np.ndarray, np.ndarray], h: float = 0.01) -> dict:
    """Delta (shares per bond) and gamma from the grid by central differences at s0 (relative step h)."""
    up, dn, mid = value_at(s0 * (1 + h), grid), value_at(s0 * (1 - h), grid), value_at(s0, grid)
    ds = s0 * h
    return {"value": mid, "delta": (up - dn) / (2 * ds), "gamma": (up - 2 * mid + dn) / ds ** 2}


def bond_floor(cb: Convertible, r: float, spread: float) -> float:
    """The straight bond: coupons and face discounted at r plus a credit spread."""
    pv = 0.0
    k = 1
    while k / cb.freq <= cb.maturity + 1e-9:
        pv += cb.face * cb.coupon / cb.freq * math.exp(-(r + spread) * k / cb.freq)
        k += 1
    return pv + cb.face * math.exp(-(r + spread) * cb.maturity)
