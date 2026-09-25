"""Power and gas trading (One Quant Book 9, chapter 23).

Real: Germany's hourly day-ahead prices and generation, 2024-2025 (Book 3's file, Bundesnetzagentur / SMARD.de,
CC BY 4.0): the price profile by hour, negative hours by year and by hour, and the slope of price on residual load
(load less wind and solar). Synthetic: intraday prices for the same hours from planted wind forecast errors; a trader
who forecasts part of the error; a 1 MW, 2 MWh battery scheduled on the day-ahead prices (perfect foresight of the
auction, as in Book 3) and re-optimised against intraday prices. NumPy and pandas.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA = ROOT.parent / "data" / "markets-3" / "de_power_hourly_2024_2025.csv"
sys.path.insert(0, str(ROOT / "firm" / "powergas"))
from firm_powergas import PowerConfig, battery, forecast_trade, intraday  # noqa: E402

YEARS = 2


@functools.lru_cache(maxsize=1)
def hourly() -> pd.DataFrame:
    d = pd.read_csv(DATA, parse_dates=["utc"])
    d["local"] = d["utc"].dt.tz_localize("UTC").dt.tz_convert("Europe/Berlin")
    d["hour"], d["year"], d["day"] = d["local"].dt.hour, d["local"].dt.year, d["local"].dt.date
    d["resid"] = (d["load"] - d["solar"] - d["wind_on"] - d["wind_off"]) / 1000          # GW
    return d


@functools.lru_cache(maxsize=1)
def days() -> np.ndarray:
    """Day-ahead prices (days, 24) of the days with 24 hours (the clock-change days dropped)."""
    return np.array([g["price"].to_numpy() for _, g in hourly().groupby("day") if len(g) == 24])


def real() -> dict:
    d = hourly()
    slope, icpt = np.polyfit(d["resid"], d["price"], 1)
    return {"mean": d.groupby("year")["price"].mean().to_dict(), "negative": (d["price"] < 0).groupby(d["year"]).sum()
            .to_dict(), "min": d.groupby("year")["price"].min().to_dict(),
            "neg_by_hour": (d["price"] < 0).groupby(d["hour"]).mean().to_dict(),
            "by_hour": d.groupby("hour")["price"].mean().to_dict(), "slope": float(slope),
            "corr": float(np.corrcoef(d["resid"], d["price"])[0, 1]), "days": len(days())}


def trade(cfg: PowerConfig | None = None) -> dict:
    """The forecast-error trade: EUR per MWh traded, share of hours traded, EUR a year per MW, and the IC."""
    cfg = cfg or PowerConfig()
    da = days()
    idp, err = intraday(da, cfg)
    f = forecast_trade(da, idp, err, cfg)
    n = np.abs(f["pos"]).sum()
    return {"per_mwh": float(f["pnl"].sum() / n), "share": float((f["pos"] != 0).mean()),
            "annual": float(f["pnl"].sum() / YEARS), "ic": f["ic"]}


def battery_table(cfg: PowerConfig | None = None) -> dict:
    """Battery revenue (EUR per MW a year): day-ahead only, and the extra from re-optimising against intraday prices."""
    cfg = cfg or PowerConfig()
    da = days()
    idp, _ = intraday(da, cfg)
    b = battery(da, cfg)
    r = battery(idp, cfg, committed=b["grid"])
    charge = b["grid"] > 0
    return {"da": float(b["cash"].sum() / YEARS), "extra": float(r["cash"].sum() / YEARS),
            "days_changed": float((r["cash"] > 1e-9).mean()), "charge_negative": float((da[charge] < 0).mean()),
            "cum_da": np.cumsum(b["cash"]), "cum_total": np.cumsum(b["cash"] + r["cash"])}
