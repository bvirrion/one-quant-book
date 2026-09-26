"""firm.lobstats -- the stylised facts of an order book, from any market-by-order stream (build of One Quant Book 10,
chapter 3). The stream is firm.tape's format (msgs: t, kind A/X/E, oid, side, price in ticks, qty; top after every
message; trades), which firm.exchsim's Result.tape() also produces.

API (stable):
    report(tape, levels=10, points=(0.001, 0.01, 0.1, 1, 10, 60)) -> dict
        depth            mean displayed shares at k ticks behind the best, bids and asks (sampled each second)
        relative         share of new orders improving / joining / k ticks behind the best, largest distance
        cancel_rates     cancellations per displayed share per second by distance from the best
        spread           time-weighted share of one-tick, two-tick and wider spreads, mean spread
        vol_per_trade    standard deviation of the mid change between consecutive trades
        cancel_life, trade_life   lifetable CDFs at `points` (seconds), the other event censoring (as SEC MIDAS)
        fleeting         share of orders cancelled in full within 2 seconds
        resilience       median seconds for the spread to return to one tick after an execution widened it
        cancel_to_trade  cancellation messages per trade
    kaplan_meier(durations, observed, points) -> list   the product-limit CDF used for the lifetables
    compare(rep, targets) -> dict                         {fact: (value, lo, hi, ok)} for targets {fact: (lo, hi)};
                                                         a fact is a report key, or "key.subkey" / "key[index]"
"""
from __future__ import annotations

import numpy as np

POINTS = (0.001, 0.01, 0.1, 1.0, 10.0, 60.0)


def kaplan_meier(durations, observed, points=POINTS) -> list[float]:
    d = np.asarray(durations, float)
    obs = np.asarray(observed, bool)
    order = np.argsort(d, kind="stable")
    d, obs = d[order], obs[order]
    n = len(d)
    surv = np.cumprod(np.where(obs, 1.0 - 1.0 / (n - np.arange(n)), 1.0))
    out = []
    for p in points:
        i = np.searchsorted(d, p, side="right") - 1
        out.append(float(1.0 - surv[i]) if i >= 0 else 0.0)
    return out


def _walk(msgs):
    """Yield (row, best_bid, best_ask, levels) before each message, maintaining displayed sizes by price."""
    levels = {1: {}, -1: {}}
    orders: dict[int, list] = {}
    for row in msgs:
        b = max(levels[1]) if levels[1] else None
        a = min(levels[-1]) if levels[-1] else None
        yield row, b, a, levels
        oid, side, px, q = int(row["oid"]), int(row["side"]), int(row["price"]), int(row["qty"])
        lv = levels[side]
        if row["kind"] == b"A":
            orders[oid] = [side, px, q]
            lv[px] = lv.get(px, 0) + q
        else:
            o = orders[oid]
            o[2] -= q
            lv[o[1]] -= q
            if lv[o[1]] == 0:
                del lv[o[1]]
            if o[2] == 0:
                del orders[oid]


def report(tape, levels: int = 10, points=POINTS) -> dict:
    msgs = tape.msgs
    seconds = float(tape.cfg.seconds)
    depth = np.zeros((2, levels))
    samples, nxt = 0, 1.0
    rel = []
    canc = np.zeros(levels)
    expo = np.zeros(levels)
    last_t = 0.0
    since: dict[int, float] = {}
    added: dict[int, tuple[float, int]] = {}
    left: dict[int, int] = {}
    ev_d, ev_kind = [], []
    fleeting = 0
    for row, b, a, lv in _walk(msgs):
        t = float(row["t"])
        both = b is not None and a is not None
        if both:
            dt = t - last_t
            if dt > 0:
                for k in range(levels):
                    expo[k] += (lv[1].get(b - k, 0) + lv[-1].get(a + k, 0)) * dt
            while t >= nxt:
                for k in range(levels):
                    depth[0, k] += lv[1].get(b - k, 0)
                    depth[1, k] += lv[-1].get(a + k, 0)
                samples += 1
                nxt += 1.0
        last_t = t
        oid, kind = int(row["oid"]), row["kind"]
        if kind == b"A":
            if both:
                px = int(row["price"])
                rel.append(b - px if row["side"] == 1 else px - a)
            since[oid], added[oid], left[oid] = t, (t, int(row["qty"])), int(row["qty"])
            continue
        if kind == b"X" and both:
            px = int(row["price"])
            k = b - px if row["side"] == 1 else px - a
            if 0 <= k < levels:
                canc[k] += int(row["qty"])
        ev_d.append(t - since[oid])
        ev_kind.append(kind)
        since[oid] = t
        left[oid] -= int(row["qty"])
        if left[oid] == 0 and kind == b"X" and t - added[oid][0] <= 2.0:
            fleeting += 1
    rel = np.array(rel)
    ev_kind = np.array(ev_kind)
    top = tape.top[tape.n_open:]
    s = top["ask"] - top["bid"]
    tt = top["t"]
    dts = np.diff(np.concatenate([tt, [seconds]]))
    tot = dts.sum()
    mid = 0.5 * (tape.top["bid"] + tape.top["ask"])
    idx = np.clip(np.searchsorted(tape.top["t"], tape.trades["t"], side="right") - 1, 0, len(mid) - 1)
    widened = np.flatnonzero((s[1:] >= 2) & (s[:-1] == 1) & (msgs["kind"][tape.n_open + 1:] == b"E")) + 1
    rec = []
    for i in widened:
        j = np.flatnonzero(s[i:] == 1)
        if len(j):
            rec.append(tt[i + j[0]] - tt[i])
    return {
        "depth": depth / max(samples, 1),
        "relative": {"improve": float(np.mean(rel < 0)), "at_best": float(np.mean(rel == 0)),
                     "behind_4": float(np.mean(rel >= 4)), "max": int(rel.max())},
        "cancel_rates": canc / np.where(expo > 0, expo, np.nan),
        "spread": {"one": float(dts[s == 1].sum() / tot), "two": float(dts[s == 2].sum() / tot),
                   "wider": float(dts[s >= 3].sum() / tot), "mean": float((s * dts).sum() / tot)},
        "vol_per_trade": float(np.std(np.diff(mid[idx]))),
        "cancel_life": kaplan_meier(ev_d, ev_kind == b"X", points),
        "trade_life": kaplan_meier(ev_d, ev_kind == b"E", points),
        "fleeting": fleeting / max(len(added), 1),
        "resilience": float(np.median(rec)) if rec else float("nan"),
        "cancel_to_trade": float(np.sum(msgs["kind"] == b"X") / max(len(tape.trades), 1)),
    }


def _get(rep, fact: str):
    if "[" in fact:
        key, i = fact[:-1].split("[")
        return rep[key][int(i)]
    if "." in fact:
        key, sub = fact.split(".")
        return rep[key][sub]
    return rep[fact]


def compare(rep: dict, targets: dict) -> dict:
    out = {}
    for fact, (lo, hi) in targets.items():
        v = float(_get(rep, fact))
        out[fact] = (v, lo, hi, bool(lo <= v <= hi))
    return out
