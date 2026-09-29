"""Book 18, chapter 20: the take-home dataset (generated, small by default) and the reference analysis.

Minute quotes and trades for synthetic stocks. Planted: a small effect of order-book imbalance on the next
minute's mid-price return, a bid-ask bounce in trade prices, and three data defects (duplicated rows, crossed
quotes, one unadjusted 2-for-1 split).
"""
import numpy as np
import pandas as pd

BETA_BP = 0.5  # planted slope: next-minute mid return (bp) per unit of imbalance
SIGMA_BP = 5.0  # minute return noise (bp)
HALF_SPREAD_BP = 3.0
SPLIT_STOCK, SPLIT_DAY = 7, 12


def generate(seed: int = 0, stocks: int = 20, days: int = 20, minutes: int = 390,
             n_dup: int = 40, n_crossed: int = 15) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(stocks):
        n = days * minutes
        imb = rng.uniform(-1, 1, n)
        ret = (BETA_BP * np.r_[0.0, imb[:-1]] + SIGMA_BP * rng.standard_normal(n)) * 1e-4
        mid = 50.0 * (1 + s / 10) * np.exp(np.cumsum(ret))
        day = np.repeat(np.arange(days), minutes)
        minute = np.tile(np.arange(minutes), days)
        if s == SPLIT_STOCK:
            mid = np.where(day >= SPLIT_DAY, mid / 2, mid)
        half = HALF_SPREAD_BP * 1e-4 * mid
        side = rng.choice([-1.0, 1.0], n)
        rows.append(pd.DataFrame({"stock": s, "day": day, "minute": minute, "bid": mid - half, "ask": mid + half,
                                  "trade": mid + side * half, "imbalance": imb}))
    df = pd.concat(rows, ignore_index=True)
    crossed = rng.choice(len(df), n_crossed, replace=False)
    df.loc[crossed, ["bid", "ask"]] = df.loc[crossed, ["ask", "bid"]].to_numpy()
    dup = df.iloc[rng.choice(len(df), n_dup, replace=False)]
    out = pd.concat([df, dup], ignore_index=True)
    return out.sort_values(["stock", "day", "minute"], kind="stable").reset_index(drop=True)


def data_checks(df: pd.DataFrame) -> dict:
    """The checks a reviewer expects on the first page of the memo."""
    dups = int(df.duplicated(["stock", "day", "minute"]).sum())
    crossed = int((df["bid"] > df["ask"]).sum())
    mid = (df["bid"] + df["ask"]) / 2
    close = df.assign(mid=mid).drop_duplicates(["stock", "day", "minute"]).groupby(["stock", "day"])["mid"].last()
    jumps = close.groupby(level=0).pct_change().abs()
    splits = [(int(s), int(d)) for (s, d), v in jumps.items() if v > 0.3]
    return {"duplicates": dups, "crossed": crossed, "splits": splits}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.drop_duplicates(["stock", "day", "minute"]).copy()
    swap = out["bid"] > out["ask"]
    out.loc[swap, ["bid", "ask"]] = out.loc[swap, ["ask", "bid"]].to_numpy()
    adj = (out["stock"] == SPLIT_STOCK) & (out["day"] >= SPLIT_DAY)
    out.loc[adj, ["bid", "ask", "trade"]] *= 2
    return out


def next_returns(df: pd.DataFrame, price: str = "mid") -> pd.DataFrame:
    d = df.copy()
    d["mid"] = (d["bid"] + d["ask"]) / 2
    g = d.groupby(["stock", "day"])[price]
    d["fwd_bp"] = (g.shift(-1) / d[price] - 1) * 1e4
    d["ret_bp"] = (d[price] / g.shift(1) - 1) * 1e4
    return d.dropna(subset=["fwd_bp", "ret_bp"])


def imbalance_slope(d: pd.DataFrame):
    """OLS slope of the next-minute return on imbalance, with a standard error clustered by stock-day."""
    x = d["imbalance"].to_numpy()
    y = d["fwd_bp"].to_numpy()
    xc = x - x.mean()
    b = float(np.dot(xc, y - y.mean()) / np.dot(xc, xc))
    resid = (y - y.mean()) - b * xc
    scores = pd.Series(xc * resid).groupby([d["stock"].to_numpy(), d["day"].to_numpy()]).sum()
    se = float(np.sqrt(np.sum(scores.to_numpy() ** 2)) / np.dot(xc, xc))
    return b, se


def lag1_autocorr(d: pd.DataFrame) -> float:
    return float(np.corrcoef(d["ret_bp"].to_numpy(), d["fwd_bp"].to_numpy())[0, 1])


def binned(d: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    edges = np.linspace(-1, 1, bins + 1)
    cat = pd.cut(d["imbalance"], edges, include_lowest=True)
    g = d.groupby(cat, observed=True)["fwd_bp"]
    out = pd.DataFrame({"centre": (edges[:-1] + edges[1:]) / 2, "mean": g.mean().to_numpy(),
                        "se": (g.std() / np.sqrt(g.count())).to_numpy()})
    return out


def calendar_cells_false_alarm(cells: int = 60, t: float = 3.1) -> float:
    """Chance that at least one of `cells` independent null cells shows |t| above t (two-sided)."""
    from scipy.stats import norm

    p = 2 * norm.sf(t)
    return 1 - (1 - p) ** cells
