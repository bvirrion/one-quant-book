"""firm.acexec -- the Almgren-Chriss execution model and the firm's scheduler interface (build of One Quant Book 10,
chapter 14).

Selling X shares over [0, T]: holdings x(t), rate v = -dx/dt. Permanent impact gamma per share traded, temporary
impact eta v (price units per share per unit rate; the chapter's local eta), volatility sigma (price units per square
root of time). Expected cost E = gamma X^2 / 2 + eta int v^2 dt, variance V = sigma^2 int x^2 dt; the trader minimises
E + lambda V.

API (stable):
    kappa(eta, sigma, lam)                       sqrt(lam sigma^2 / eta): the urgency
    trajectory(X, T, kappa_, t)                  continuous optimum x(t) = X sinh(kappa (T - t)) / sinh(kappa T)
                                                 (a straight line when kappa = 0)
    discrete(X, T, n, eta, sigma, lam)           the discrete optimum on n intervals (Almgren and Chriss
                                                 2000): holdings x_0..x_n, with the discrete urgency given by
                                                 cosh(kappa~ tau) = 1 + lam sigma^2 tau^2 / (2 eta)
    cost_var(holdings, T, gamma, eta, sigma)     expected cost and variance of any discrete schedule
    frontier(X, T, n, gamma, eta, sigma, lams)   (E, V) of the optimal schedules for several risk aversions
    time_to(share, kappa, T)                     when the optimal trajectory has traded that share of the order
    Scheduler                                    the interface chapters 15, 16 and 28 implement: targets(times) ->
                                                 holdings at those times; ACScheduler, LinearScheduler
"""
from __future__ import annotations

import math

import numpy as np


def kappa(eta: float, sigma: float, lam: float) -> float:
    return math.sqrt(lam * sigma**2 / eta)


def trajectory(x_total: float, horizon: float, k: float, t) -> np.ndarray:
    t = np.asarray(t, float)
    if k * horizon < 1e-9:
        return x_total * (1 - t / horizon)
    return x_total * np.sinh(k * (horizon - t)) / np.sinh(k * horizon)


def discrete(x_total: float, horizon: float, n: int, eta: float, sigma: float,
             lam: float) -> np.ndarray:
    tau = horizon / n
    t = np.arange(n + 1) * tau
    if lam == 0:
        return x_total * (1 - t / horizon)
    kt = math.acosh(1 + lam * sigma**2 * tau**2 / (2 * eta)) / tau
    return x_total * np.sinh(kt * (horizon - t)) / np.sinh(kt * horizon)


def cost_var(holdings, horizon: float, gamma: float, eta: float,
             sigma: float) -> tuple[float, float]:
    x = np.asarray(holdings, float)
    tau = horizon / (len(x) - 1)
    trades = -np.diff(x)
    cost = 0.5 * gamma * x[0] ** 2 + eta * float(np.sum(trades**2)) / tau
    var = sigma**2 * tau * float(np.sum(x[1:] ** 2))
    return cost, var


def frontier(x_total, horizon, n, gamma, eta, sigma, lams):
    return [cost_var(discrete(x_total, horizon, n, eta, sigma, lam), horizon, gamma, eta, sigma) for lam in lams]


def time_to(share: float, k: float, horizon: float) -> float:
    """When the optimal trajectory has traded `share` of the order: x(t) = (1 - share) X."""
    if k * horizon < 1e-9:
        return share * horizon
    return float(horizon - math.asinh((1 - share) * math.sinh(k * horizon)) / k)


class Scheduler:
    """Target holdings (shares still to trade, signed) at given times from the start."""

    def targets(self, times) -> np.ndarray:
        raise NotImplementedError


class ACScheduler(Scheduler):
    def __init__(self, x_total: float, horizon: float, k: float):
        self.x, self.h, self.k = x_total, horizon, k

    def targets(self, times):
        return trajectory(self.x, self.h, self.k, np.minimum(np.asarray(times, float), self.h))


class LinearScheduler(ACScheduler):
    def __init__(self, x_total: float, horizon: float):
        super().__init__(x_total, horizon, 0.0)
