"""A synthetic option chain with dividends and skew, and what can be read back from it (Chapter 25)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/parity"))
from firm_parity import implied_dividends_pv, implied_forward, implied_vol, price, variance_strip

SPOT, RATE, YEARS = 100.0, 0.04, 0.25
DIVIDEND, DIV_TIME = 0.80, 0.10


def true_forward() -> float:
    return (SPOT - DIVIDEND * math.exp(-RATE * DIV_TIME)) * math.exp(RATE * YEARS)


def true_vol(strike: float) -> float:
    """A skewed smile: higher volatility for low strikes."""
    x = math.log(strike / true_forward())
    return 0.20 - 0.30 * x + 0.50 * x * x


def chain(strikes: list[float], cents: bool = True) -> list[tuple[float, float, float]]:
    """(strike, call mid, put mid), rounded to the cent as a screen would show them."""
    f = true_forward()
    out = []
    for k in strikes:
        c, p = price(f, k, YEARS, RATE, true_vol(k), "C"), price(f, k, YEARS, RATE, true_vol(k), "P")
        out.append((k, round(c, 2), round(p, 2)) if cents else (k, c, p))
    return out


def read_chain(rows: list[tuple[float, float, float]]):
    """From screen prices alone: the implied forward at each strike, their average, the implied
    dividend, and the implied volatility of the out-of-the-money option at each strike."""
    forwards = [implied_forward(c, p, k, YEARS, RATE) for k, c, p in rows]
    f = sum(forwards) / len(forwards)
    vols = []
    for k, c, p in rows:
        right, premium = ("P", p) if k < f else ("C", c)
        vols.append(implied_vol(premium, f, k, YEARS, RATE, right))
    return forwards, f, implied_dividends_pv(SPOT, f, YEARS, RATE), vols


def index_style(strikes: list[float]) -> float:
    """Model-free 'volatility index' of the synthetic chain, in volatility points."""
    f = true_forward()
    k0 = max(k for k in strikes if k <= f)
    quotes = []
    for k, c, p in chain(strikes, cents=False):
        quotes.append((k, p if k < k0 else c if k > k0 else 0.5 * (c + p)))
    return 100.0 * math.sqrt(variance_strip(f, YEARS, RATE, quotes))
