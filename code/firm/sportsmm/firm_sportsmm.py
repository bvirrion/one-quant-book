"""firm.sportsmm -- sports and prediction market making in play (One Quant Book 11, chapter 26).

Built on Book 3's firm.odds (odds and implied probabilities). A football match is priced with independent Poisson
goals (home and away rates per 90 minutes); in play, the probability of a home win is updated from the score and the
time left. A market maker quotes the home-win contract (a claim paying 1 if the home side wins) on an exchange at
its fair probability -+ a half-spread, `size` units each side. When a goal is scored, courtsiders at the ground act
after a short latency; the market maker's data feed reports the goal after its own latency and it cancels at once;
the exchange holds every in-play order for the bet delay before matching it. Recreational bettors trade at the quote
throughout and pay the half-spread.

API (stable):
    home_win(lh, la, t_left, score_diff, max_goals)   P(home win) with Poisson goals over the time left (fractions of
                                                      90 minutes)
    Match(lh, la, seed)                               goal times and sides for one simulated match
    trade_match(match, delay_s, mm_lat, fast_lat, size, half_spread, rec_per_min, rec_stake, cap)
                                                      the market maker's P&L: spread from recreational bets, losses to
                                                      courtsiders at goals, and how many goals were sniped
    season(n, delay_s, seed, ...)                     many matches: loss per goal, spread per match, net
    odds_quote(p, half_spread)                        decimal odds on both sides of the maker's quote and its overround
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "odds"))
import firm_odds as fo  # noqa: E402


def _pois(k: int, m: float) -> float:
    return math.exp(-m) * m**k / math.factorial(k)


def home_win(lh: float, la: float, t_left: float, score_diff: int = 0, max_goals: int = 12) -> float:
    ph = [_pois(k, lh * t_left) for k in range(max_goals)]
    pa = [_pois(k, la * t_left) for k in range(max_goals)]
    return sum(ph[i] * pa[j] for i in range(max_goals) for j in range(max_goals) if score_diff + i - j > 0)


class Match:
    def __init__(self, lh: float = 1.5, la: float = 1.1, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.lh, self.la = lh, la
        nh, na = rng.poisson(lh), rng.poisson(la)
        times = np.concatenate([rng.uniform(0, 90, nh), rng.uniform(0, 90, na)])
        sides = np.concatenate([np.ones(nh), -np.ones(na)])
        order = np.argsort(times)
        self.times, self.sides = times[order], sides[order]
        self.z = rng.standard_normal((len(times), 2))


def trade_match(m: Match, delay_s: float = 5.0, mm_lat: float = 3.0, fast_lat: float = 0.5, size: float = 1000.0,
                half_spread: float = 0.01, rec_per_min: float = 2.0, rec_stake: float = 50.0,
                cap: float | None = None, lat_sd: float = 0.3) -> dict:
    """Latencies are lognormal around their medians (log standard deviation lat_sd). A courtsider's order matches
    if it arrives, after the bet delay, before the market maker's cancel; it takes min(size, cap) at the stale quote
    and the market maker loses that stake times the probability's jump (less the half-spread)."""
    diff, loss, sniped, goals = 0, 0.0, 0, 0
    for g, (t, side) in enumerate(zip(m.times, m.sides, strict=True)):
        left = (90.0 - t) / 90.0
        before = home_win(m.lh, m.la, left, diff)
        diff += int(side)
        after = home_win(m.lh, m.la, left, diff)
        goals += 1
        a_fast = fast_lat * math.exp(lat_sd * m.z[g, 0])
        a_mm = mm_lat * math.exp(lat_sd * m.z[g, 1])
        if a_fast + delay_s < a_mm:
            q = size if cap is None else min(size, cap)
            loss += q * max(abs(after - before) - half_spread, 0.0)
            sniped += 1
    spread = 90.0 * rec_per_min * rec_stake * half_spread
    return {"spread": spread, "loss": loss, "net": spread - loss, "goals": goals, "sniped": sniped}


def season(n: int = 2000, delay_s: float = 5.0, seed: int = 0, **kw) -> dict:
    tot = {"spread": 0.0, "loss": 0.0, "net": 0.0, "goals": 0, "sniped": 0}
    for i in range(n):
        r = trade_match(Match(seed=seed * 100003 + i), delay_s=delay_s, **kw)
        for k in tot:
            tot[k] += r[k]
    g = max(tot["goals"], 1)
    return {"loss_per_goal": tot["loss"] / g, "sniped_share": tot["sniped"] / g, "spread_per_match": tot["spread"] / n,
            "net_per_match": tot["net"] / n, "goals_per_match": tot["goals"] / n}


def odds_quote(p: float, half_spread: float) -> tuple[float, float, float]:
    """Decimal odds a bettor gets to back the home win (the maker lays at p + h), to back 'not home win' (the maker
    lays the other side at 1 - p + h), and the resulting book's overround (firm.odds), 2h."""
    back_home, back_not = 1.0 / (p + half_spread), 1.0 / (1.0 - p + half_spread)
    return back_home, back_not, fo.overround([back_home, back_not])
