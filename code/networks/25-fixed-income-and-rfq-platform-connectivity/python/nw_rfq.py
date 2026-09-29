"""Chapter 25 of One Quant Book 14: two seconds to answer (firm.rfqlink, labelled simulation).

    OURS, THEIRS              the dealer's auto-responder pipeline and its four competitors' (assumptions)
    TIMER_MS, N_DEALERS       the client's quote timer and the number of dealers asked
    rules_at(ours)            win, missed and lost-to-speed shares under the three client rules
    curves(grid)              our win rate against our pricing stage's median, for each rule
    values()                  what halving the pricing time and bidding one cent better are worth, per rule
    miss_curves(timers)       the chance of missing the timer against its length, with and without manual answers
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "rfqlink"))
import firm_rfqlink as rl  # noqa: E402

S = rl.Stage
OURS = rl.Pipeline((S("network in", 0.5, 0.3), S("FIX engine", 0.1, 0.3), S("pricing", 20.0, 0.8),
                    S("risk and limits", 1.0, 0.5), S("network out", 0.5, 0.3)), manual_share=0.02)
THEIRS = rl.Pipeline(tuple(S(s.name, 50.0 if s.name == "pricing" else s.median_ms, s.sigma) for s in OURS.stages),
                     manual_share=0.02)
TIMER_MS, N_DEALERS, K = 2000.0, 5, 3
RULES = ("expiry", "first_k", "first_ok")
GRID = tuple(rl.log_grid(1.0, 1000.0, 4))


def with_pricing(median_ms):
    return rl.Pipeline(tuple(S(s.name, median_ms if s.name == "pricing" else s.median_ms, s.sigma)
                             for s in OURS.stages), OURS.manual_share)


def rules_at(ours=OURS):
    return {r: rl.auction(N_DEALERS, ours, THEIRS, r, TIMER_MS, K) for r in RULES}


def curves(grid=GRID):
    return {r: [rl.auction(N_DEALERS, with_pricing(m), THEIRS, r, TIMER_MS, K)["win"] for m in grid] for r in RULES}


def values():
    return {r: rl.value_of(N_DEALERS, OURS, THEIRS, r, with_pricing(10.0), timer_ms=TIMER_MS, k=K) for r in RULES}


TIMERS = tuple(rl.log_grid(100.0, 30000.0, 4))


def miss_curves(timers=TIMERS):
    auto = rl.Pipeline(OURS.stages, manual_share=0.0)
    return {"ours": [rl.miss_prob(OURS, t) for t in timers], "auto": [rl.miss_prob(auto, t) for t in timers]}
