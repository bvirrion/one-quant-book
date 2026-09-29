"""The research library function promoted from the chapter 15 notebook: one calculation, its choices as
arguments."""
from __future__ import annotations

import pandas as pd


def average_growth(df: pd.DataFrame, threshold: float = 90.0, since: int | None = None,
                   exclude=(), weight: str = "country") -> float:
    """Average growth of country-years with debt above `threshold` (percent of output).

    weight='country': the mean of each country's mean (each country counts once);
    weight='country-year': the pooled mean of the country-years. `since` drops earlier
    years and `exclude` drops countries: the caller states both, no notebook remembers them."""
    d = df[df["debt"] > threshold]
    if since is not None:
        d = d[d["year"] >= since]
    if len(exclude):
        d = d[~d["country"].isin(list(exclude))]
    if weight == "country":
        return float(d.groupby("country")["growth"].mean().mean())
    if weight == "country-year":
        return float(d["growth"].mean())
    raise ValueError(weight)
