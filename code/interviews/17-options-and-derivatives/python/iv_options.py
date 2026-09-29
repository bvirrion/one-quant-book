"""Book 18, chapter 17: Black-Scholes prices and Greeks for the chapter's option questions (scipy.stats.norm)."""
from math import exp, log, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.stats import norm


def d1d2(s, k, sigma, t, r=0.0, q=0.0):
    d1 = (log(s / k) + (r - q + sigma * sigma / 2) * t) / (sigma * sqrt(t))
    return d1, d1 - sigma * sqrt(t)


def call(s, k, sigma, t, r=0.0, q=0.0):
    d1, d2 = d1d2(s, k, sigma, t, r, q)
    return s * exp(-q * t) * norm.cdf(d1) - k * exp(-r * t) * norm.cdf(d2)


def put(s, k, sigma, t, r=0.0, q=0.0):
    d1, d2 = d1d2(s, k, sigma, t, r, q)
    return k * exp(-r * t) * norm.cdf(-d2) - s * exp(-q * t) * norm.cdf(-d1)


def gamma(s, k, sigma, t, r=0.0):
    d1, _ = d1d2(s, k, sigma, t, r)
    return norm.pdf(d1) / (s * sigma * sqrt(t))


def vega(s, k, sigma, t, r=0.0):
    d1, _ = d1d2(s, k, sigma, t, r)
    return s * norm.pdf(d1) * sqrt(t)


def digital(s, k, sigma, t, r=0.0):
    _, d2 = d1d2(s, k, sigma, t, r)
    return exp(-r * t) * norm.cdf(d2)


def digital_vega(s, k, sigma, t, h=1e-5):
    return (digital(s, k, sigma + h, t) - digital(s, k, sigma - h, t)) / (2 * h)


def parity_gap(c, p, s, k, r, t, pv_div=0.0):
    """Quoted C - P minus its no-arbitrage value S - PV(div) - K e^{-rT}."""
    return (c - p) - (s - pv_div - k * exp(-r * t))


def fair_variance_smile(sigma_of_k, s=100.0, t=1.0, lo=1.0, hi=1000.0):
    """Fair variance of a variance swap (zero rates): (2/T) [int_0^S P(K)/K^2 dK + int_S^inf C(K)/K^2 dK]."""
    f_put = quad(lambda k: put(s, k, sigma_of_k(k), t) / k**2, lo, s, limit=400)[0]
    f_call = quad(lambda k: call(s, k, sigma_of_k(k), t) / k**2, s, hi, limit=400)[0]
    return 2 / t * (f_put + f_call)


def gamma_curve(spots, k, sigma, t):
    return np.array([gamma(s, k, sigma, t) for s in spots])
