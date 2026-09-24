"""One trader's day, three P&L numbers (Chapter 7)."""
import pathlib
import sys
from collections import deque

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/pnl"))
from firm_pnl import BUY, SELL, Position

U = 10_000  # ledger units per dollar

# (time, side, quantity, price in dollars, mid at that time)
FILLS = [
    ("09:35", BUY, 20_000, 49.30, 49.32),
    ("10:10", BUY, 20_000, 49.55, 49.56),
    ("11:20", SELL, 10_000, 50.10, 50.08),
    ("13:05", BUY, 10_000, 49.70, 49.72),
    ("14:30", SELL, 25_000, 50.28, 50.26),
    ("15:40", BUY, 15_000, 50.20, 50.22),
]
LAST_TRADE, CLOSING_MID, OFFICIAL_CLOSE = 50.30, 50.00, 50.00
FEES, FINANCING = 3_400.0, 600.0


def units(dollars: float) -> int:
    return round(dollars * U)


def replay(fills=FILLS) -> Position:
    p = Position()
    for _, side, qty, price, _ in fills:
        p.on_fill(side, qty, units(price))
    return p


def three_numbers() -> dict[str, float]:
    p = replay()
    return {
        "trader": p.total(units(LAST_TRADE)) / U,                       # marks at the last print, gross
        "risk": p.total(units(CLOSING_MID)) / U,                        # marks at the closing mid, gross
        "finance": p.total(units(OFFICIAL_CLOSE)) / U - FEES - FINANCING,   # official close, net
    }


def fifo(fills=FILLS, mark: float = CLOSING_MID) -> tuple[float, float]:
    """Realised and unrealised P&L in dollars under first-in-first-out (long-only day)."""
    lots: deque[list[float]] = deque()
    realised = 0.0
    for _, side, qty, price, _ in fills:
        if side == BUY:
            lots.append([qty, price])
            continue
        left = qty
        while left > 0:
            lot = lots[0]
            take = min(left, lot[0])
            realised += take * (price - lot[1])
            lot[0] -= take
            left -= take
            if lot[0] == 0:
                lots.popleft()
    return realised, sum(q * (mark - px) for q, px in lots)


def explain(open_qty: int, prev_close: float, close: float, fills, fees: float, financing: float):
    """Daily P&L split: carried position (close to close), new trades (fill to close), costs."""
    carried = open_qty * (close - prev_close)
    new = sum(side * qty * (close - price) for _, side, qty, price, _ in fills)
    return {"carried position": carried, "new trades": new, "fees": -fees, "financing": -financing,
            "total": carried + new - fees - financing}


def fx_split(qty: int, p0: float, p1: float, x0: float, x1: float) -> dict[str, float]:
    """P&L in base currency of a foreign position: price, currency and cross terms."""
    return {"price": qty * (p1 - p0) * x0, "currency": qty * p0 * (x1 - x0),
            "cross": qty * (p1 - p0) * (x1 - x0), "total": qty * (p1 * x1 - p0 * x0)}
