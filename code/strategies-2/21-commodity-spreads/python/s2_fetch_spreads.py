"""Crack and location spreads from EIA spot prices, 2006-2026 (One Quant Book 9, chapter 21).

Downloads from FRED the EIA daily spot prices of WTI (Cushing) and Brent (Europe) crude oil ($/bbl) and New York
Harbor conventional gasoline and ultra-low-sulphur diesel ($/gal), keeps the days on which all four are published
(from 14 June 2006), and forms the 3-2-1 crack spread ((2 gasoline + 1 diesel) x 42 / 3 - WTI, $/bbl), the gasoline
crack (gasoline x 42 - WTI) and the Brent-WTI spread. It writes only statistics: WTI's lowest price with its date;
each spread's mean, standard deviation, minimum and maximum with dates, daily AR(1) persistence and half-life, the
correlation of its daily changes with WTI's; a mean-reversion rule on the 3-2-1 crack and on Brent-WTI (short when
the spread is more than 1.5 standard deviations above its trailing 250-day mean, long when below, out when it
crosses the mean; a cost of $0.10/bbl per unit traded), with its annual P&L, Sharpe ratio, share of days in the
market, best and worst days and the correlation of its daily P&L with WTI's daily change; the same without April
2020, when WTI's spot price turned negative, and with the trade entered a day later; the autocorrelation of each
spread's daily changes; the change of the gasoline crack from the first trading day of February to the last of April
in each year 2007-2026; and each spread's monthly mean. Spot assessments are not tradable prices: the rule is an
optimistic proxy. Output in data/strategies-2: spreads_summary.csv, spreads_monthly.csv. Run once.
"""
from __future__ import annotations

import io
import math
import pathlib
import time
import urllib.request

import numpy as np
import pandas as pd

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"
SERIES = {"wti": "DCOILWTICO", "brent": "DCOILBRENTEU", "gas": "DGASNYH", "ulsd": "DDFUELNYH"}
COST = 0.10


def _get(url: str) -> bytes:
    time.sleep(1)
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def rule(x: pd.Series, band: float = 1.5, window: int = 250, delay: int = 1):
    """Daily P&L ($/bbl) of fading the spread's deviation from its trailing mean, with costs; the position decided on
    a day's close earns from `delay` days later."""
    z = ((x - x.rolling(window).mean()) / x.rolling(window).std()).to_numpy()
    pos, cur = np.zeros(len(x)), 0.0
    for t, v in enumerate(z):
        if np.isfinite(v):
            if v > band:
                cur = -1.0
            elif v < -band:
                cur = 1.0
            elif cur != 0 and np.sign(v) == cur:
                cur = 0.0
        pos[t] = cur
    held = np.concatenate([np.zeros(delay), pos[:-delay]])
    pnl = held * x.diff().fillna(0).to_numpy() - COST * np.abs(np.diff(np.concatenate([[0.0], pos])))
    return pd.Series(pnl, index=x.index), pos


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cols = {}
    for k, sid in SERIES.items():
        df = pd.read_csv(io.BytesIO(_get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")))
        df.columns = ["date", "v"]
        cols[k] = pd.to_numeric(df.set_index(pd.to_datetime(df["date"]))["v"], errors="coerce")
    p = pd.DataFrame(cols).dropna()
    spreads = {"crack321": (2 * p["gas"] + p["ulsd"]) * 42 / 3 - p["wti"], "gascrack": p["gas"] * 42 - p["wti"],
               "brentwti": p["brent"] - p["wti"]}
    dwti = p["wti"].diff()
    rows = [("first", str(p.index[0].date())), ("last", str(p.index[-1].date())), ("days", len(p)),
            ("wti_min", float(p["wti"].min())), ("wti_min_date", str(p["wti"].idxmin().date()))]
    for name, x in spreads.items():
        phi = float(np.corrcoef(x.to_numpy()[:-1], x.to_numpy()[1:])[0, 1])
        rows += [(f"{name}_mean", float(x.mean())), (f"{name}_sd", float(x.std())),
                 (f"{name}_min", float(x.min())), (f"{name}_min_date", str(x.idxmin().date())),
                 (f"{name}_max", float(x.max())), (f"{name}_max_date", str(x.idxmax().date())),
                 (f"{name}_phi", phi), (f"{name}_halflife", math.log(0.5) / math.log(phi)),
                 (f"{name}_corr_dwti", float(x.diff().corr(dwti)))]
        if name != "gascrack":
            pnl, pos = rule(x)
            live = pnl[pnl.index >= pnl.index[250]]
            rows += [(f"{name}_rule_annual", float(live.mean() * 252)),
                     (f"{name}_rule_sr", float(live.mean() / live.std() * math.sqrt(252))),
                     (f"{name}_rule_inmarket", float((pos[250:] != 0).mean())),
                     (f"{name}_rule_corr_dwti", float(live.corr(dwti[live.index]))),
                     (f"{name}_rule_worst", float(live.min())), (f"{name}_rule_worst_date", str(live.idxmin().date()))]
            ex = live[(live.index < "2020-04-01") | (live.index >= "2020-05-01")]
            late = rule(x, delay=2)[0][live.index]
            late = late[(late.index < "2020-04-01") | (late.index >= "2020-05-01")]
            rows += [(f"{name}_rule_late_sr_ex_apr2020", float(late.mean() / late.std() * math.sqrt(252))),
                     (f"{name}_ac1_changes", float(x.diff().autocorr(1)))]
            rows += [(f"{name}_rule_sr_ex_apr2020", float(ex.mean() / ex.std() * math.sqrt(252))),
                     (f"{name}_rule_annual_ex_apr2020", float(ex.mean() * 252)),
                     (f"{name}_rule_best", float(live.max())), (f"{name}_rule_best_date", str(live.idxmax().date()))]
    g = spreads["gascrack"]
    ch = []
    for y in range(2007, 2027):
        feb, apr = g[(g.index >= f"{y}-02-01") & (g.index < f"{y}-03-01")], g[(g.index >= f"{y}-04-01")
                                                                               & (g.index < f"{y}-05-01")]
        if len(feb) and len(apr):
            ch.append(apr.iloc[-1] - feb.iloc[0])
    ch = np.array(ch)
    rows += [("season_years", len(ch)), ("season_mean", float(ch.mean())), ("season_up", int((ch > 0).sum())),
             ("season_t", float(ch.mean() / ch.std(ddof=1) * math.sqrt(len(ch)))), ("season_worst", float(ch.min()))]
    pd.DataFrame(rows, columns=["key", "value"]).to_csv(OUT / "spreads_summary.csv", index=False)
    m = pd.DataFrame(spreads).resample("MS").mean().round(2)
    m.index = m.index.strftime("%Y-%m")
    m.index.name = "month"
    m.to_csv(OUT / "spreads_monthly.csv")


if __name__ == "__main__":
    main()
