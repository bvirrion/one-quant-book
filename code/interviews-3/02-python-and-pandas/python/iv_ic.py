def daily_ic(df):
    """df: date, symbol, price, signal. Rank correlation of signal and next return."""
    df = df.sort_values(["symbol", "date"])
    nxt = df.groupby("symbol").price.shift(-1)           # within a symbol only
    df = df.assign(fwd=nxt / df.price - 1).dropna(subset=["signal", "fwd"])
    r = df.groupby("date")[["signal", "fwd"]].rank()     # ranks among complete rows
    r = r - r.groupby(df["date"]).transform("mean")
    num = (r["signal"] * r["fwd"]).groupby(df["date"]).sum()
    sxx = (r["signal"] ** 2).groupby(df["date"]).sum()
    syy = (r["fwd"] ** 2).groupby(df["date"]).sum()
    return num / (sxx * syy) ** 0.5
