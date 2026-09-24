"""Book 3, Chapter 19: inverse option premiums in coin and in dollars, the delta that includes the premium
currency, the annualised basis of dated futures, and the carry of long spot ETF, short regulated future.
Snapshot numbers are those quoted in the chapter's dated boxes (24 September 2026)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/cryptoopt"))
from firm_cryptoopt import (  # noqa: E402
    annualised_basis,
    coin_premium,
    etf_basis_carry,
    forward_delta,
    premium_adjusted_delta,
    return_on_margin,
)

INDEX = 83_499.12
FUTURES = {"25DEC26": (84_533.98, 92), "26MAR27": (85_668.78, 183), "25JUN27": (86_833.65, 274),
           "24SEP27": (87_948.30, 365)}                 # price, days to expiry (rounded)
F_DEC, T_DEC = 84_538.67, 91.87 / 365
SMILE = {60_000: 0.4711, 70_000: 0.4076, 80_000: 0.3820, 90_000: 0.3746, 100_000: 0.3811,
         110_000: 0.3960, 120_000: 0.4219}


def basis_table() -> list[tuple[str, int, float]]:
    return [(e, d, annualised_basis(f, INDEX, d)) for e, (f, d) in FUTURES.items()]


def delta_table() -> list[tuple[int, float, float, float, float]]:
    """(strike, call premium in coin, call premium in dollars, forward delta, premium-adjusted delta)."""
    out = []
    for k, v in SMILE.items():
        c = coin_premium(F_DEC, k, T_DEC, v, "C")
        out.append((k, c, c * F_DEC, forward_delta(F_DEC, k, T_DEC, v, "C"),
                    premium_adjusted_delta(F_DEC, k, T_DEC, v, "C")))
    return out


def expiry_value_coin(f: float, k: float, right: str) -> float:
    """Value in coin at expiry of an inverse option: (F - K)+ / F for a call, (K - F)+ / F for a put."""
    return max(f - k, 0.0) / f if right == "C" else max(k - f, 0.0) / f


def scenarios() -> dict[str, tuple[float, float]]:
    """Carry and return on capital of long ETF, short future, for two basis levels (illustrative financing
    of 4.5%, the fund's 0.25% fee, 0.30% a year of futures costs, 25% futures margin, 10% ETF haircut)."""
    out = {}
    for name, b in (("rich", 0.10), ("snapshot", annualised_basis(*FUTURES["25DEC26"][:1], INDEX, 92))):
        c = etf_basis_carry(b, 0.045, 0.0025, 0.003)
        out[name] = (c, return_on_margin(c, 0.25, 0.10))
    return out
