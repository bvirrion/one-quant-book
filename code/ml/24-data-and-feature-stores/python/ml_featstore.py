"""Data and feature stores (One Quant Book 12, chapter 24).

Twelve order-book features declared once (firm.featstore), computed offline over eight thirty-minute firm.tape
sessions and online by streaming the same messages, at every trade. Four planted skews between research and
production: research that sees one event past the decision, research on one-second bars (the value at the end of the
decision's second), production that stores features in float32, and production that receives trade prints 200 ms late.
For each: the share of decisions where the stores disagree, the rate at which a sampled parity check catches it, and
what it does to a ridge forecast of the mid's change over the next second (and five) (rank IC and P&L per decision,
trained on four sessions, tested on the other four)."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("featstore", "tape"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_featstore import FeatureDef, events_from_tape, offline, parity, stream  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

FEATURES = (FeatureDef("spread", "spread", "last"), FeatureDef("imbalance", "imbalance", "last"),
            FeatureDef("depth imbalance", "depth", "last"), FeatureDef("weighted mid minus mid", "wmid", "last"),
            FeatureDef("OFI 5 s", "ofi", "sum", 5), FeatureDef("OFI 30 s", "ofi", "sum", 30),
            FeatureDef("volume 30 s", "trade_qty", "sum", 30),
            FeatureDef("signed volume 30 s", "trade_sign", "sum", 30),
            FeatureDef("trades 10 s", "is_trade", "sum", 10), FeatureDef("mid change 5 s", "mid", "change", 5),
            FeatureDef("mid change 30 s", "mid", "change", 30), FeatureDef("messages 10 s", "one", "sum", 10))
SESSIONS, SECONDS, HORIZON = range(8), 1800.0, 1.0
TRADE_INPUTS = ("trade_qty", "trade_sign", "is_trade")


@functools.lru_cache(maxsize=16)
def session(s, horizon=HORIZON):
    ev = events_from_tape(simulate(TapeConfig(seconds=SECONDS, news_at=None, seed=900 + s)))
    ev["is_trade"] = ev["is_trade"].astype(float)
    times = np.unique(ev["t"][ev["is_trade"] > 0])
    times = times[times < SECONDS - 30.0]
    k0 = np.searchsorted(ev["t"], times, side="right") - 1
    k1 = np.searchsorted(ev["t"], times + horizon, side="right") - 1
    return ev, times, ev["mid"][k1] - ev["mid"][k0]


def research(s, skew=None):
    ev, times, _ = session(s)
    if skew == "one event ahead":
        return offline(ev, FEATURES, times, lag_events=1)
    if skew == "one-second bars":
        return offline(ev, FEATURES, np.ceil(times))
    return offline(ev, FEATURES, times)


def _late(ev, delay):
    """The event table production sees when trade prints arrive `delay` seconds after the book update."""
    t_trd = ev["t"][ev["is_trade"] > 0] + delay
    t = np.r_[ev["t"], t_trd]
    order = np.argsort(t, kind="stable")
    out = {"t": t[order]}
    n = len(ev["t"])
    for k, v in ev.items():
        if k == "t":
            continue
        if k in TRADE_INPUTS:
            out[k] = np.r_[np.zeros(n), v[ev["is_trade"] > 0]][order]
        elif k in ("ofi", "one"):
            out[k] = np.r_[v, np.zeros(len(t_trd))][order]
        else:                                                           # book state: carried to the late rows
            carry = np.r_[v, v[np.searchsorted(ev["t"], t_trd, side="right") - 1]]
            out[k] = carry[order]
    return out


@functools.lru_cache(maxsize=40)
def production(s, skew=None):
    ev, times, _ = session(s)
    if skew == "late trade prints":
        return stream(_late(ev, 0.2), FEATURES, times)
    on = stream(ev, FEATURES, times)
    if skew == "float32 storage":
        on = on.astype(np.float32).astype(np.float64)
    return on


SKEWS = ("one event ahead", "one-second bars", "float32 storage", "late trade prints")


@functools.lru_cache(maxsize=2)
def parity_table(sample=5, checks=5, tol=1e-9):
    """Mismatch share (tolerance 1e-9) and detection rate of a check on `sample` random decisions, over 8 sessions x 5
    checks, for each skew; and for the clean pair."""
    out = {}
    for skew in (None,) + SKEWS:
        shares, flags = [], []
        for s in SESSIONS:
            off = research(s, skew if skew in ("one event ahead", "one-second bars") else None)
            on = production(s, skew if skew in ("float32 storage", "late trade prints") else None)
            shares.append(parity(off, on, tol)["mismatch share"])
            flags += [parity(off, on, tol, sample=sample, seed=c)["flagged"] for c in range(checks)]
        out[skew or "none"] = (float(np.mean(shares)), float(np.mean(flags)))
    return out


def _fit(Xs, ys):
    X, y = np.vstack(Xs), np.concatenate(ys)
    mu, sd = X.mean(0), X.std(0) + 1e-12
    Z = (X - mu) / sd
    b = np.linalg.solve(Z.T @ Z + 10.0 * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return lambda A: ((A - mu) / sd) @ b


def _score(f, Xs, ys):
    from scipy.stats import spearmanr

    p, y = np.concatenate([f(X) for X in Xs]), np.concatenate(ys)
    return float(spearmanr(p, y)[0]), float(np.mean(np.sign(p) * y))


@functools.lru_cache(maxsize=2)
def model_effects(horizon=HORIZON):
    """Train on sessions 0-3 with each research pipeline; report the research backtest on sessions 4-7 (its own
    features) and the live result (production features, clean or skewed)."""
    tr, te = SESSIONS[:4], SESSIONS[4:]
    y_tr = [session(s, horizon)[2] for s in tr]
    y_te = [session(s, horizon)[2] for s in te]
    out = {}
    for skew in (None,) + SKEWS:
        res_skew = skew if skew in ("one event ahead", "one-second bars") else None
        prod_skew = skew if skew in ("float32 storage", "late trade prints") else None
        f = _fit([research(s, res_skew) for s in tr], y_tr)
        back = _score(f, [research(s, res_skew) for s in te], y_te)
        live = _score(f, [production(s, prod_skew) for s in te], y_te)
        out[skew or "none"] = {"backtest IC": back[0], "backtest P&L": back[1], "live IC": live[0], "live P&L": live[1]}
    return out


def counts():
    return {"decisions": int(sum(len(session(s)[1]) for s in SESSIONS)),
            "messages": int(sum(len(session(s)[0]["t"]) for s in SESSIONS))}


@functools.lru_cache(maxsize=1)
def feature_skew():
    """For each skew and feature: the share of decisions where research and production differ (tolerance 1e-9), and
    the root mean square difference as a share of the feature's standard deviation, over all sessions."""
    out = {}
    for skew in SKEWS:
        res_skew = skew if skew in ("one event ahead", "one-second bars") else None
        prod_skew = skew if skew in ("float32 storage", "late trade prints") else None
        off = np.vstack([research(s, res_skew) for s in SESSIONS])
        on = np.vstack([production(s, prod_skew) for s in SESSIONS])
        d = off - on
        out[skew] = {f.name: (float(np.mean(np.abs(d[:, j]) > 1e-9)),
                              float(np.sqrt(np.mean(d[:, j] ** 2)) / on[:, j].std())) for j, f in enumerate(FEATURES)}
    return out


def train_on_production(skew="one-second bars", horizon=HORIZON):
    """Exercise 7: the one-second model trained on the features production actually computes (clean online values),
    against the one trained on research's skewed features, both scored live."""
    tr, te = SESSIONS[:4], SESSIONS[4:]
    y_tr = [session(s, horizon)[2] for s in tr]
    y_te = [session(s, horizon)[2] for s in te]
    f_prod = _fit([production(s) for s in tr], y_tr)
    f_res = _fit([research(s, skew) for s in tr], y_tr)
    return {"trained on production": _score(f_prod, [production(s) for s in te], y_te)[0],
            "trained on research": _score(f_res, [production(s) for s in te], y_te)[0]}
