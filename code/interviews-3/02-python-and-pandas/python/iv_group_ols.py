import pandas as pd


def group_betas(df: pd.DataFrame) -> pd.Series:
    d = df.dropna(subset=["x", "y"])          # a row counts only if it has both
    means = d.groupby("symbol")[["x", "y"]].transform("mean")
    dx, dy = d["x"] - means["x"], d["y"] - means["y"]
    by = d["symbol"]
    sxx = (dx * dx).groupby(by).sum()
    flat = sxx <= 1e-24 * (d["x"] * d["x"]).groupby(by).sum()    # constant x, up to rounding
    return ((dx * dy).groupby(by).sum() / sxx).mask(flat)
