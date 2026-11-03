import pandas as pd


def quotes_at_trades(trades, quotes):
    return pd.merge_asof(
        trades.sort_values("t"), quotes.sort_values("t"),
        on="t", by="symbol", direction="backward",
    )
