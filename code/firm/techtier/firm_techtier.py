"""firm.techtier -- latency tiers as a strategic choice: what each tier costs, what it earns strategy by strategy, and
the arms race when every firm chooses (build of One Quant Book 16, chapter 19).

Tier costs: venue fees from One Quant Book 14's published fee schedules (firm.colobill, each item sourced in that
book's ledger) plus the firm's own hardware, network and people, which are inputs. When Book 14's connectivity plan
(firm.connplan) provides a dated cost table, `Tier.venue_annual` takes it instead.

Races: a strategy's revenue pool V is split between races (a share alpha) and everything else. Races go to the
firms in the fastest tier present, shared equally among them; the rest is shared equally among all firms. A firm's
revenue is V (alpha P(win) + (1 - alpha) / n). The arms race: firms in turn choose their best tier against the
others' until no one changes (best-response dynamics); the waste is the extra spending over everyone at the
cheapest tier, as a share of the equilibrium's spending, since the races only move the same pool between firms.

API (stable):
    Tier(name, venue_annual, other_annual) ; colobill_venue_fees(footprints) -> {name: annual venue fees}
    Strategy(name, pool, alpha) ; revenue(strategy, mine, others) ; best_tier(strategy, tiers, others)
    arms_race(strategy, tiers, n, start) -> (profile, rounds) ; waste(strategy, tiers, n) -> dict
    run_change(items) -> (run, change, run share)
"""
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "colobill"))
import firm_colobill as cb  # noqa: E402


@dataclass(frozen=True)
class Tier:
    name: str
    venue_annual: float
    other_annual: float

    @property
    def annual(self):
        return self.venue_annual + self.other_annual


def colobill_venue_fees(footprints, term_months=36):
    """footprints: {tier name: [(schedule key, [(item, qty), ...]), ...]} -> {tier name: annual venue fees}."""
    return {name: sum(cb.bill(cb.SCHEDULES[k], fp, term_months)["annual"] for k, fp in parts)
            for name, parts in footprints.items()}


@dataclass(frozen=True)
class Strategy:
    name: str
    pool: float            # revenue available to all competitors a year
    alpha: float           # share of the pool decided by speed races


def revenue(s, mine, others):
    """mine, others: tier indices (higher is faster)."""
    n = 1 + len(others)
    top = max([mine, *others])
    p_win = 1 / (1 + sum(o == top for o in others)) if mine == top else 0.0
    return s.pool * (s.alpha * p_win + (1 - s.alpha) / n)


def best_tier(s, tiers, others):
    profits = [revenue(s, i, others) - t.annual for i, t in enumerate(tiers)]
    return max(range(len(tiers)), key=lambda i: (profits[i], -i)), profits


def arms_race(s, tiers, n, start=0, max_rounds=100):
    """Best-response dynamics from everyone at tier `start`; raises if they cycle (no pure equilibrium found)."""
    prof = [start] * n
    for rounds in range(1, max_rounds + 1):
        changed = False
        for i in range(n):
            b, _ = best_tier(s, tiers, prof[:i] + prof[i + 1:])
            if b != prof[i]:
                prof[i], changed = b, True
        if not changed:
            return prof, rounds
    raise RuntimeError("best responses cycle: no pure equilibrium reached")


def waste(s, tiers, n):
    prof, _ = arms_race(s, tiers, n)
    spend = sum(tiers[i].annual for i in prof)
    base = n * tiers[0].annual
    profits = [revenue(s, prof[i], prof[:i] + prof[i + 1:]) - tiers[prof[i]].annual for i in range(n)]
    return {"profile": sorted(prof, reverse=True), "spend": spend, "baseline": base,
            "wasted_share": (spend - base) / spend if spend else 0.0, "industry_profit": s.pool - spend,
            "baseline_profit": s.pool - base, "profits": profits}


def run_change(items):
    """items: [(name, amount, 'run' | 'change')] -> (run total, change total, run share)."""
    run = sum(a for _, a, k in items if k == "run")
    change = sum(a for _, a, k in items if k == "change")
    return run, change, run / (run + change)
