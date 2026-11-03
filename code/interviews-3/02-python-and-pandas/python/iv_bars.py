import pandas as pd


def minute_bars(prices: pd.Series) -> pd.DataFrame:
    bars = prices.resample("1min", label="right", closed="left").ohlc()
    bars["close"] = bars["close"].ffill()
    return bars
