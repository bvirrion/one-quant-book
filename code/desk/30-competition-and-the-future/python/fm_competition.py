"""One Quant Book 16, chapter 30: moats, concentration and free entry.

The public figures: six wholesalers and the top two's 66% share (SEC Release 34-96495) bound the index. The model: a
symmetric Cournot market with S = (a - c)^2 / b and a fixed cost F per firm (illustrative book parameters), the
free-entry number of firms and the planner's, the index against F, and a merger of two of the six firms.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/moats"))
import firm_moats as fm  # noqa: E402

WHOLESALERS, TOP2 = 6, 0.66          # SEC Release 34-96495 (ledger 30 F1)
S, F = 3000.0, 50.0                  # $ million: the market's surplus scale and a firm's fixed cost (illustrative)
A, C = 10.0, 4.0                     # demand intercept and marginal cost (basis points)
B = (A - C) ** 2 / S


def public_bounds():
    return fm.hhi_bounds(WHOLESALERS, TOP2, 2)


def entry(fixed=F, surplus=S):
    n = fm.free_entry(surplus, fixed)
    return {"n": n, "hhi": 10_000 / n, "planner": fm.planner(surplus, fixed),
            "profit": surplus / (n + 1) ** 2 - fixed, "w_free": fm.welfare(surplus, fixed, n),
            "w_plan": fm.welfare(surplus, fixed, fm.planner(surplus, fixed))}


def merger(synergy=0.0):
    pre = fm.cournot(A, B, [C] * 6)
    post = fm.merge(A, B, [C] * 6, 0, 1, synergy)
    return {"pre": pre, "post": post, "net_pre": 2 * (pre["profit"][0] - F), "net_post": post["profit"][-1] - F,
            "needed": fm.synergy_for_price(A, [C] * 6, 0, 1)}
