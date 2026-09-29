"""firm.posttrade -- confirmation matching, settlement instructions, reconciliation and breaks (Book 15, ch. 22).

After a trade is booked (chapter 21) it must be agreed with the counterparty and settled. This module matches the
firm's trades with the counterparties' confirmations (candidate pairs on key fields, then every compared field within
its tolerance: matched, a partial match with a score and the fields that differ, or unmatched on either side),
generates settlement instructions from a table of standard settlement instructions, reconciles positions or cash
with a custodian's statement (one-to-one, and one-to-many when the custodian reports a block the firm allocated), and
classifies and ages the breaks. Quantities are integers, prices floats in currency units, times in hours.

API (stable):
    match(ours, theirs, keys, tolerances) -> MatchResult(matched, partial, ours_only, theirs_only)
        ours, theirs: [dict]; keys: fields that must be equal to pair; tolerances {field: absolute tolerance}
    match_rate(result, n) -> share of ours matched automatically
    SSITable({(counterparty, market): ssi}).instruction(trade, our_account) -> dict (or KeyError: no SSI)
    reconcile(ours {key: qty}, theirs {key: qty}, groups=None) -> [Break]       groups {their key: [our keys]}
    Break(kind, key, ours, theirs, opened, owner) ; classify(ours, theirs) -> kind ; age(breaks, now) -> {bucket: n}
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MatchResult:
    matched: list = field(default_factory=list)          # (ours, theirs)
    partial: list = field(default_factory=list)          # (ours, theirs, score, [fields that differ])
    ours_only: list = field(default_factory=list)
    theirs_only: list = field(default_factory=list)


def _differs(a: dict, b: dict, tolerances: dict) -> list[str]:
    out = []
    for f, tol in tolerances.items():
        x, y = a.get(f), b.get(f)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            if abs(x - y) > tol + 1e-12:
                out.append(f)
        elif x != y:
            out.append(f)
    return out


def match(ours: list, theirs: list, keys: tuple, tolerances: dict) -> MatchResult:
    """Pair each trade with the confirmation that agrees on the keys and differs in the
    fewest fields (ties: the first); all within tolerance is a match, else partial."""
    res = MatchResult()
    pool: dict = {}
    for i, t in enumerate(theirs):
        pool.setdefault(tuple(t[k] for k in keys), []).append(i)
    used = set()
    for o in ours:
        cands = [i for i in pool.get(tuple(o[k] for k in keys), []) if i not in used]
        if not cands:
            res.ours_only.append(o)
            continue
        best = min(cands, key=lambda i: (len(_differs(o, theirs[i], tolerances)), i))
        used.add(best)
        diff = _differs(o, theirs[best], tolerances)
        if diff:
            score = 1 - len(diff) / len(tolerances)
            res.partial.append((o, theirs[best], score, diff))
        else:
            res.matched.append((o, theirs[best]))
    res.theirs_only = [t for i, t in enumerate(theirs) if i not in used]
    return res


def match_rate(res: MatchResult, n: int) -> float:
    return len(res.matched) / n if n else 0.0


class SSITable:
    """Standard settlement instructions: where each counterparty settles each market, kept once."""

    def __init__(self, table: dict):
        self.table = table

    def instruction(self, trade: dict, our_account: str) -> dict:
        ssi = self.table[(trade["counterparty"], trade["market"])]
        buy = trade["side"] == 1
        return {"type": "receive versus payment" if buy else "deliver versus payment",
                "security": trade["symbol"], "quantity": trade["qty"],
                "amount": round(trade["qty"] * trade["price"], 2),
                "settle_date": trade["settle_date"], "our_account": our_account, "their_agent": ssi["agent"],
                "their_account": ssi["account"]}


@dataclass
class Break:
    kind: str
    key: tuple
    ours: float
    theirs: float
    opened: float = 0.0
    owner: str = ""


def classify(ours, theirs) -> str:
    if ours is None:
        return "missing in our books"
    if theirs is None:
        return "missing at the custodian"
    return "quantity difference"


def reconcile(ours: dict, theirs: dict, groups: dict | None = None,
              opened: float = 0.0) -> list[Break]:
    """Compare quantities by key; `groups` maps a custodian key to several of ours
    (a block the firm allocated)."""
    ours, theirs = dict(ours), dict(theirs)
    for tk, oks in (groups or {}).items():
        total = sum(ours.pop(k, 0) for k in oks)
        ours[tk] = ours.get(tk, 0) + total
    out = []
    for k in sorted(set(ours) | set(theirs), key=str):
        a, b = ours.get(k), theirs.get(k)
        if a != b:
            x, y = (a if a is not None else 0), (b if b is not None else 0)
            out.append(Break(classify(a, b), k, x, y, opened))
    return out


BUCKETS = ((0, 24, "under 1 day"), (24, 72, "1 to 3 days"), (72, 168, "3 to 7 days"), (168, 1e9, "over 7 days"))


def age(breaks: list[Break], now: float) -> dict:
    out = {b: 0 for _, _, b in BUCKETS}
    for br in breaks:
        a = now - br.opened
        out[next(name for lo, hi, name in BUCKETS if lo <= a < hi)] += 1
    return out
