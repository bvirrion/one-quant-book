"""Chapter 18 of Book 2: emerging-market FX and NDFs. An NDF settled against its fixing, the basis
between onshore and offshore forwards, a central-parity band, and the Swiss franc's floor and its
end in 2015 (ECB reference rates). NDF, onshore and offshore quotes are illustrative."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/ndf"))
from firm_ndf import band, fixing_date, implied_local_rate, leveraged_loss, ndf_settlement, onshore_offshore_basis

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"


def krw_ndf() -> dict[str, float]:
    settle = dt.date(2026, 10, 13)
    return {"settlement": ndf_settlement(10e6, 1380.00, 1425.50),
            "seller": ndf_settlement(10e6, 1380.00, 1425.50, buyer=False),
            "fixing_day": fixing_date(settle, set()).toordinal(), "if_1350": ndf_settlement(10e6, 1380.00, 1350.00)}


def cny_cnh(r_usd: float = 0.0368) -> dict[str, float]:
    on = implied_local_rate(7.1000, 7.0400, r_usd, 91)
    off = implied_local_rate(7.1200, 7.0700, r_usd, 91)
    return {"onshore": on, "offshore": off, "basis": onshore_offshore_basis(7.1000, 7.0400, 7.1200, 7.0700, r_usd, 91),
            "band_lo": band(7.1000, 0.02)[0], "band_hi": band(7.1000, 0.02)[1]}


def load_eurchf() -> list[tuple[str, float]]:
    with open(DATA / "eurchf_ecb_2010_2016.csv") as f:
        return [(r["date"], float(r["eurchf"])) for r in csv.DictReader(f)]


def unpeg(notional_eur: float = 1e6, leverage: float = 20.0) -> dict[str, float]:
    rates = dict(load_eurchf())
    before, after = rates["2015-01-14"], rates["2015-01-15"]
    move = 1.0 - after / before
    margin = notional_eur * before / leverage
    loss = notional_eur * (before - after)
    return {"before": before, "after": after, "move": move, "margin": margin, "loss": loss,
            "multiple": leveraged_loss(move, leverage), "negative_balance": loss - margin,
            "low_month": min(v for d, v in rates.items() if d.startswith("2015-01")),
            "by_leverage": {k: leveraged_loss(move, k) for k in (5, 10, 20, 50)}}
