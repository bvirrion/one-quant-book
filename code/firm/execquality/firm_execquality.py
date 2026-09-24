"""firm.execquality -- execution-quality report (build of Chapter 10, One Quant Book 1).

Integer prices (ledger units). Half-spreads are reported in basis points of the mid and price
improvement in ledger units per share; every mean is share-weighted.
"""
from collections import defaultdict
from dataclasses import dataclass

SIZE_BUCKETS = ((1, 99), (100, 499), (500, 1999), (2000, 4999), (5000, 10**12))


@dataclass(frozen=True)
class Fill:
    ts: int
    symbol: str
    side: int            # +1 buy, -1 sell
    quantity: int
    price: int
    bid: int
    ask: int


def size_bucket(quantity: int) -> str:
    for lo, hi in SIZE_BUCKETS:
        if lo <= quantity <= hi:
            return f"{lo}-{hi}" if hi < 10**12 else f"{lo}+"
    raise ValueError("non-positive quantity")


def score(fill: Fill, mid2_later: int) -> dict[str, int]:
    """Per-fill measures in half ledger units (twice the mid keeps everything an integer)."""
    mid2 = fill.bid + fill.ask
    effective2 = fill.side * (2 * fill.price - mid2)
    realised2 = fill.side * (2 * fill.price - mid2_later)
    impact2 = fill.side * (mid2_later - mid2)
    assert effective2 == realised2 + impact2
    quote = fill.ask if fill.side > 0 else fill.bid
    return {"effective2": effective2, "realised2": realised2, "impact2": impact2,
            "improvement": fill.side * (quote - fill.price), "mid2": mid2}


def report(fills, mid2_at, horizon: int, by=("symbol", "size_bucket")) -> dict:
    """mid2_at(symbol, ts) -> bid + ask at that time. Returns {group: stats, "_excluded": n}."""
    acc = defaultdict(lambda: defaultdict(float))
    excluded = 0
    for f in fills:
        if f.bid <= 0 or f.ask <= 0 or f.bid >= f.ask:
            excluded += 1
            continue
        s = score(f, mid2_at(f.symbol, f.ts + horizon))
        key = tuple(f.symbol if k == "symbol" else size_bucket(f.quantity) for k in by)
        a = acc[key]
        a["fills"] += 1
        a["shares"] += f.quantity
        for k in ("effective2", "realised2", "impact2"):
            a[k + "_bp"] += f.quantity * s[k] / s["mid2"] * 1e4      # x2 / x2 cancels: basis points
        a["improvement"] += f.quantity * s["improvement"]
        where = "inside" if s["improvement"] > 0 else ("at" if s["improvement"] == 0 else "outside")
        a[where] += f.quantity
    out = {}
    for key, a in acc.items():
        n = a["shares"]
        out[key] = {"fills": int(a["fills"]), "shares": int(n),
                    "effective_bp": a["effective2_bp"] / n, "realised_bp": a["realised2_bp"] / n,
                    "impact_bp": a["impact2_bp"] / n, "improvement": a["improvement"] / n,
                    "inside": a["inside"] / n, "at": a["at"] / n, "outside": a["outside"] / n}
    out["_excluded"] = excluded
    return out
