"""Book 18, chapter 29: every number spoken in the six mock interviews, and the two coding answers."""
from collections import OrderedDict
from math import exp, log, sqrt

import numpy as np
from scipy.stats import norm


# Interview 1: trader at a market maker
def heads_market(seen_heads: int, seen: int, total: int = 20):
    rest = total - seen
    return seen_heads + rest / 2, sqrt(rest * 0.25)


def kelly_even_money(p):
    return 2 * p - 1


# Interview 2: researcher at a systematic fund
def ic_t_stat(ic, n_days):
    return ic * sqrt(n_days)


# Interview 3: developer at a proprietary firm
class LRUCache:
    """Fixed-capacity least-recently-used cache: O(1) get and put with an ordered dict."""

    def __init__(self, capacity: int):
        self.cap, self.d = capacity, OrderedDict()

    def get(self, key):
        if key not in self.d:
            return None
        self.d.move_to_end(key)
        return self.d[key]

    def put(self, key, value):
        self.d[key] = value
        self.d.move_to_end(key)
        if len(self.d) > self.cap:
            self.d.popitem(last=False)


def token_bucket(arrivals, rate, burst):
    """Messages allowed by a token bucket (tokens refill at `rate` per second up to `burst`); arrivals are times."""
    tokens, last, sent = float(burst), 0.0, []
    for t in arrivals:
        tokens = min(burst, tokens + (t - last) * rate)
        last = t
        if tokens >= 1:
            tokens -= 1
            sent.append(t)
    return sent


# Interview 4: machine-learning engineer
def psi(expected, actual):
    e, a = np.asarray(expected, float), np.asarray(actual, float)
    return float(np.sum((a - e) * np.log(a / e)))


# Interview 5: bank quant
def forward(s, r, q, t):
    return s * exp((r - q) * t)


def bs_call(s, k, sigma, t, r=0.0):
    d1 = (log(s / k) + (r + sigma * sigma / 2) * t) / (sigma * sqrt(t))
    return s * norm.cdf(d1) - k * exp(-r * t) * norm.cdf(d1 - sigma * sqrt(t))


def vega(s, k, sigma, t):
    d1 = (log(s / k) + sigma * sigma / 2 * t) / (sigma * sqrt(t))
    return s * norm.pdf(d1) * sqrt(t)


def digital_by_spread(s, k, sigma, t, h):
    return (bs_call(s, k - h, sigma, t) - bs_call(s, k + h, sigma, t)) / (2 * h)


# Interview 6: portfolio-manager hire
MONTHLY = [1.2, -0.4, 0.8, 2.1, -1.5, 0.3, 1.0, -2.2, 1.7, 0.6, -0.9, 1.4,
           0.5, 1.1, -0.7, 0.9, 1.6, -1.8, 0.4, 1.3, -0.2, 0.8, 1.9, -1.1]  # per cent, the candidate's two years


def sharpe_and_drawdown(monthly_pct):
    r = np.asarray(monthly_pct) / 100
    sharpe = r.mean() / r.std(ddof=1) * sqrt(12)
    wealth = np.cumprod(1 + r)
    dd = (wealth / np.maximum.accumulate(np.r_[1.0, wealth])[1:] - 1).min()
    return sharpe, dd


def net_sharpe(gross_sharpe, vol, turnover, cost_bp):
    return (gross_sharpe * vol - turnover * cost_bp / 1e4) / vol


def prob_hit_drawdown(mu, sigma, a, t):
    """P(min over [0, t] of mu s + sigma W_s <= -a): Brownian motion with drift."""
    s = sigma * sqrt(t)
    return norm.cdf((-a - mu * t) / s) + exp(-2 * mu * a / sigma**2) * norm.cdf((-a + mu * t) / s)


# Follow-up questions
def token_bucket_queue(arrivals, rate, burst):
    """Departure times when messages that find no token wait in a FIFO queue instead of being dropped."""
    tokens, clock, out = float(burst), 0.0, []
    for t in arrivals:
        start = max(t, out[-1] if out else 0.0)
        tokens = min(burst, tokens + (start - clock) * rate)
        clock = start
        if tokens < 1:
            wait = (1 - tokens) / rate
            clock += wait
            tokens = 1.0
        tokens -= 1
        out.append(clock)
    return out


def bloom_bits(n, fp):
    """Bits and hash functions of a Bloom filter holding n keys at false-positive rate fp."""
    m = -n * log(fp) / log(2) ** 2
    return m, m / n * log(2)


def forward_discrete_dividend(s, r, div, t_div, t):
    return (s - div * exp(-r * t_div)) * exp(r * t)
