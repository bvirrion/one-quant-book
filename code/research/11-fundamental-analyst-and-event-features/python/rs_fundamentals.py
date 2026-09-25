"""Fundamental, analyst and event features (One Quant Book 7, chapter 11).

Real data: ten large US companies' diluted EPS facts and filing calendars from SEC EDGAR (rs_fetch_edgar.py): the days
from each fiscal period's end to the earnings release (8-K item 2.02) and to the 10-Q or 10-K filing, the reported
values that changed in later filings and how many of those were share splits, and Apple's trailing-twelve-month EPS as
first reported against today's view. Synthetic data (firm.synthmkt): the information coefficient of an earnings
surprise and of book-to-price keyed on the date they became known, against the same features keyed on the period end.
NumPy and pandas only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("fundpit", "synthmkt"):
    sys.path.insert(0, str(ROOT / c))
from firm_fundpit import days_to_event, load, quarterly, restated, split_ratio, ttm  # noqa: E402
from firm_synthmkt import simulate  # noqa: E402

DATA = pathlib.Path(__file__).resolve().parents[4] / "data" / "research"
NAMES = {320193: "Apple", 789019: "Microsoft", 104169: "Walmart", 21344: "Coca-Cola", 200406: "Johnson & Johnson",
         34088: "Exxon Mobil", 80424: "Procter & Gamble", 50863: "Intel", 354950: "Home Depot", 320187: "Nike"}
Q, H = 63, 21                                   # synthmkt quarter length and the feature's horizon (days)


# ------------------------------------------------------------------------------------------------ EDGAR
@functools.lru_cache(maxsize=1)
def edgar():
    eps = pd.read_csv(DATA / "edgar_eps.csv")
    fil = pd.read_csv(DATA / "edgar_filings.csv")
    return eps, fil


def calendar(since: str = "2013-01-01"):
    """Per fiscal period end (10-Q or 10-K period since `since`): days to the first earnings release after it and to
    the report's own filing."""
    _, fil = edgar()
    rows = []
    for cik, g in fil.groupby("cik"):
        rel = g.loc[g.form == "8-K", "filed"].tolist()
        rep = g[g.form.isin(["10-Q", "10-K"]) & (g.period >= since)]
        d_rel = days_to_event(rep.period.tolist(), rel, 90)
        d_fil = (pd.to_datetime(rep.filed) - pd.to_datetime(rep.period)).dt.days.to_numpy()
        for (_, r), a, b in zip(rep.iterrows(), d_rel, d_fil, strict=True):
            rows.append({"name": NAMES[cik], "form": r.form, "period": r.period, "release": a, "filing": b})
    return pd.DataFrame(rows)


def calendar_summary():
    c = calendar()
    by = c[c.form == "10-Q"].groupby("name")[["release", "filing"]].agg(["median", "std"])
    q, k = c[c.form == "10-Q"], c[c.form == "10-K"]
    return {"periods": len(c), "matched": int(c.release.notna().sum()), "by_name": by,
            "q_release": float(q.release.median()), "q_filing": float(q.filing.median()),
            "k_release": float(k.release.median()), "k_filing": float(k.filing.median()),
            "q_filing_max": float(q.filing.max()), "k_filing_max": float(k.filing.max()),
            "same_day": float((c.release == c.filing).mean()), "gap": float((c.filing - c.release).median())}


def release_to_filing():
    """Per company, first three fiscal quarters: share of 10-Qs filed on the release day, and the median days from
    release to filing for the others (exercise 7)."""
    q = calendar()
    q = q[q.form == "10-Q"].dropna()
    same = q.release == q.filing
    return {n: (float(same[q.name == n].mean()), float((q.filing - q.release)[(q.name == n) & ~same].median()))
            for n in sorted(q.name.unique())}


def facts():
    eps, _ = edgar()
    return [{"entity": int(r.cik), "start": r.start, "end": r.end, "val": r.val, "filed": r.filed}
            for r in eps.itertuples()]


@functools.lru_cache(maxsize=1)
def store():
    return load(facts())


def restatements():
    """Quarterly EPS values that changed in a later filing, per company, and how many changed by a split ratio."""
    s = store()
    out = {}
    for cik, name in NAMES.items():
        r = restated(s, cik, "eps_Q")
        splits = [x for x in r if split_ratio(x[1], x[2]) is not None]
        out[name] = {"changed": len(r), "splits": len(splits),
                     "ratios": sorted({split_ratio(x[1], x[2]) for x in splits}),
                     "other": [(x[0], x[1], x[2]) for x in r if split_ratio(x[1], x[2]) is None]}
    return out


def apple_ttm():
    """Apple's TTM diluted EPS at each quarter end: as first known (each quarter's value from its first filing) and
    as known today (after the 2020 four-for-one split rescaled the history)."""
    s = store()
    first = {}
    for end in quarterly(s, 320193, "eps", "9999-12-31"):
        k = s.first(320193, "eps_Q", end)
        if k is not None:
            first[end] = k[1]
        else:                                             # a fourth quarter: the year minus nine months, first filed
            fy = s.first(320193, "eps_FY", end)
            nine = [s.first(320193, "eps_9M", k2) for k2 in quarterly(s, 320193, "eps", "9999-12-31")
                    if 80 <= (pd.Timestamp(end) - pd.Timestamp(k2)).days <= 100]
            if fy is not None and nine and nine[0] is not None:
                first[end] = fy[1] - nine[0][1]
    return ttm(first), ttm(quarterly(s, 320193, "eps", "9999-12-31"))


# ------------------------------------------------------------------------------------------------ synthmkt
@functools.lru_cache(maxsize=1)
def panel():
    return simulate()


def _ic(x, y) -> float:
    ok = ~np.isnan(x) & ~np.isnan(y)
    rx, ry = np.argsort(np.argsort(x[ok])), np.argsort(np.argsort(y[ok]))
    return float(np.corrcoef(rx, ry)[0, 1])


def _fwd(P, t0: np.ndarray, pid: np.ndarray) -> np.ndarray:
    """Market-adjusted return over the H days after day t0 (NaN if the listing ends or the panel does)."""
    adj = P.ret - P.beta[None, :] * P.mkt[:, None]
    out = np.full(len(t0), np.nan)
    for i, (t, p) in enumerate(zip(t0, pid, strict=True)):
        if t + H < adj.shape[0]:
            out[i] = np.sum(adj[t + 1:t + H + 1, p])
    return out


def ic_inflation():
    """Quarterly cross-sections of (a) the earnings surprise, known on the announcement day, and (b) book-to-price, the
    book value known on its filing day (with the price of the filing day, or of the period end): mean rank IC with the
    next 21 days' market-adjusted return, keyed on the day the number became known and keyed on the period's end."""
    P = panel()
    ev = np.array(P.earnings)
    t, p, s = ev[:, 0].astype(int), ev[:, 1].astype(int), ev[:, 2]
    f = t - t % Q                                                 # the quarter the announcement reports on
    head = t - f
    out = {"head_mean": float(head.mean()), "head_median": float(np.median(head)),
           "in_window": float(np.mean((head >= 1) & (head <= H)))}
    for name, key in (("sue_known", t), ("sue_end", f)):
        y = _fwd(P, key, p)
        ics = [_ic(s[f == q], y[f == q]) for q in np.unique(f) if (f == q).sum() > 100]
        out[name], out[name + "_se"] = float(np.mean(ics)), float(np.std(ics, ddof=1) / np.sqrt(len(ics)))
    fund = pd.DataFrame([x for x in P.fundamentals if x["field"] == "book"])
    fund = fund[fund.filed + H < P.ret.shape[0]]
    for name, col, px in (("bp_known", "filed", "filed"), ("bp_known_stale", "filed", "fiscal_end"),
                          ("bp_end", "fiscal_end", "fiscal_end")):
        key, pid = fund[col].to_numpy(), fund.pid.to_numpy()
        bp = fund.value.to_numpy() / P.price[fund[px].to_numpy(), pid]
        y = _fwd(P, key, pid)
        q = fund.fiscal_end.to_numpy()
        ics = [_ic(bp[q == v], y[q == v]) for v in np.unique(q)]
        out[name], out[name + "_se"] = float(np.mean(ics)), float(np.std(ics, ddof=1) / np.sqrt(len(ics)))
    out["quarters"] = len(ics)
    return out
