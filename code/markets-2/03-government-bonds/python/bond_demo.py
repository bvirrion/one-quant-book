"""Chapter 3 of Book 2: government bonds. Two illustrative US notes (a five-year and a ten-year),
their price-yield curves, a year of clean and dirty prices, a bootstrapped zero curve, and the
numbers of the weekend problem."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from firm_bond import Bond, bootstrap_par

SETTLE = dt.date(2026, 9, 25)
TEN = Bond(4.25, dt.date(2036, 8, 15))      # illustrative ten-year note
FIVE = Bond(4.00, dt.date(2031, 9, 30))     # illustrative five-year note (month-end schedule)
Y10, Y5 = 0.0420, 0.0395


def to_32nds(price: float) -> str:
    """Treasury quote: handle, 32nds, and '+' for a half (a 64th), rounded to the nearest 64th."""
    n64 = round(price * 64)
    handle, rest = divmod(n64, 64)
    thirty_seconds, half = divmod(rest, 2)
    return f"{handle}-{thirty_seconds:02d}{'+' if half else ''}"


def from_32nds(quote: str) -> float:
    handle, frac = quote.split("-")
    half = frac.endswith("+")
    return int(handle) + (int(frac.rstrip("+")) + (0.5 if half else 0.0)) / 32


def price_yield_curve(bond: Bond, y0: float, settle: dt.date = SETTLE) -> list[tuple[float, float, float, float]]:
    """(yield %, price, duration line, duration + convexity) around y0, dirty prices."""
    r = bond.risk(y0, settle)
    out = []
    for i in range(-100, 101):
        dy = i * 0.0010 / 4                          # -2.5% ... +2.5% in 2.5 bp steps
        p = bond.dirty_price(y0 + dy, settle)
        lin = r["dirty"] * (1 - r["modified"] * dy)
        quad = r["dirty"] * (1 - r["modified"] * dy + 0.5 * r["convexity"] * dy * dy)
        out.append((100 * (y0 + dy), p, lin, quad))
    return out


def year_of_prices(bond: Bond, y: float, start: dt.date = dt.date(2026, 8, 15)) -> list[tuple[int, float, float]]:
    """(day, clean, dirty) every day for a year at a constant yield."""
    out = []
    for k in range(0, 365):
        d = start + dt.timedelta(days=k)
        out.append(((d - start).days, bond.clean_price(y, d), bond.dirty_price(y, d)))
    return out


PAR = [0.0395, 0.0393, 0.0392, 0.0392, 0.0393, 0.0395, 0.0397, 0.0399, 0.0401, 0.0404,
       0.0406, 0.0408, 0.0410, 0.0412, 0.0414, 0.0416, 0.0418, 0.0419, 0.0420, 0.0421]   # 0.5y ... 10y


def zero_curve() -> list[tuple[float, float, float]]:
    """(years, par yield %, zero rate % semiannual) from the illustrative par curve."""
    dfs = bootstrap_par(PAR)
    out = []
    for k, (p, df) in enumerate(zip(PAR, dfs, strict=True), start=1):
        t = k / 2
        z = 2 * (df ** (-1 / (2 * t)) - 1)
        out.append((t, 100 * p, 100 * z))
    return out


def hedge(face_long: float = 100e6, settle: dt.date = SETTLE) -> dict[str, float]:
    """Long the five-year, short the ten-year in the face that neutralises DV01."""
    r5, r10 = FIVE.risk(Y5, settle), TEN.risk(Y10, settle)
    face_short = face_long * r5["dv01"] / r10["dv01"]

    def value(y5: float, y10: float) -> float:
        return face_long / 100 * FIVE.dirty_price(y5, settle) - face_short / 100 * TEN.dirty_price(y10, settle)

    v0 = value(Y5, Y10)
    return {
        "face_short": face_short, "ratio": face_short / face_long,
        "dv01_5_per_m": r5["dv01"] * 1e4, "dv01_10_per_m": r10["dv01"] * 1e4,
        "pnl_up1": value(Y5 + 1e-4, Y10 + 1e-4) - v0,
        "pnl_up25": value(Y5 + 0.0025, Y10 + 0.0025) - v0,
        "pnl_dn25": value(Y5 - 0.0025, Y10 - 0.0025) - v0,
        "pnl_5up10": value(Y5 + 0.0010, Y10) - v0,
        "pnl_10up10": value(Y5, Y10 + 0.0010) - v0,
        "conv5": r5["convexity"], "conv10": r10["convexity"],
        "net_cash": v0,
    }

