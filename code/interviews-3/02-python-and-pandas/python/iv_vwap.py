import pandas as pd


def vwap_by_symbol_day(df: pd.DataFrame) -> pd.Series:
    money = df["price"] * df["qty"]
    keys = [df["symbol"], df["day"]]
    return money.groupby(keys).sum() / df["qty"].groupby(keys).sum()
