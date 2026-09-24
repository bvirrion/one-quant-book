"""Chapter 31 of Book 2: reading a macro calendar and a rates screen. The September 2026 calendar
with the FOMC blackout; Treasury yield moves on payroll days against other days (H.15 data,
2023-2026); curve slopes and fly; a DV01-neutral 2s10s steepener sized with the chapter 3 bond
calculator (illustrative 2- and 10-year notes) and its P&L under two real payroll-day moves; and
the sensitivity of yields to data surprises on synthetic data."""
import csv
import datetime as dt
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/macrocal"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from firm_bond import Bond
from firm_macrocal import (
    Event,
    calendar,
    classify,
    curve_summary,
    dv01_neutral,
    event_day_moves,
    sensitivity,
    steepener_pnl,
)

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"
SETTLE = dt.date(2026, 9, 22)
TWO, TEN = Bond(4.625, dt.date(2028, 8, 31)), Bond(4.875, dt.date(2036, 8, 15))   # illustrative notes
SHORT_TEN = 100e6
MOVES = {"2024-08-02": (-28.0, -19.0), "2024-10-04": (23.0, 13.0)}                # H.15, bp


def daily() -> tuple[list[str], list[float], list[float]]:
    rows = list(csv.DictReader(open(DATA / "ust_2y10y_daily.csv")))
    return [r["date"] for r in rows], [float(r["y2"]) for r in rows], [float(r["y10"]) for r in rows]


def payroll_dates() -> set[str]:
    return {r["date"] for r in csv.DictReader(open(DATA / "bls_empsit_release_dates.csv"))}


def curve_rows() -> list[dict[str, str]]:
    return list(csv.DictReader(open(DATA / "ust_curve_daily.csv")))


def september_2026() -> list[tuple[Event, bool]]:
    events = [Event(dt.date(2026, 9, 4), "08:30 ET", "employment report (August)"),
              Event(dt.date(2026, 9, 11), "08:30 ET", "CPI (August)"),
              Event(dt.date(2026, 9, 16), "FOMC", "FOMC decision (meeting 15-16)")]
    return calendar(events, [(dt.date(2026, 9, 15), dt.date(2026, 9, 16))])


def event_stats() -> dict[str, float]:
    dates, y2, y10 = daily()
    start = dates.index("2023-01-03") - 1
    dates, y2, y10 = dates[start:], y2[start:], y10[start:]
    pay = payroll_dates()
    a = event_day_moves(dates, y2, pay)
    b = event_day_moves(dates, y10, pay)
    s = event_day_moves(dates, [x - y for x, y in zip(y10, y2, strict=True)], pay)
    return {"on2": a[0], "off2": a[1], "on10": b[0], "off10": b[1], "on_s": s[0], "off_s": s[1],
            "n_on": a[2], "n_off": a[3]}


def payroll_moves() -> list[tuple[str, float, float, str]]:
    dates, y2, y10 = daily()
    pay, out = payroll_dates(), []
    for k in range(1, len(dates)):
        if dates[k] in pay:
            d2, d10 = 100 * (y2[k] - y2[k - 1]), 100 * (y10[k] - y10[k - 1])
            out.append((dates[k], d2, d10, classify(d2, d10)))
    return out


def screen() -> dict[str, dict[str, float]]:
    rows = {r["date"]: r for r in curve_rows()}
    return {d: curve_summary(*(float(rows[d][k]) for k in ("y2", "y5", "y10", "y30")))
            for d in ("2025-09-22", "2026-03-23", "2026-09-22")}


def problem() -> dict[str, float]:
    r2, r10 = TWO.risk(0.0471, SETTLE), TEN.risk(0.0496, SETTLE)
    long_two = dv01_neutral(r10["dv01"], r2["dv01"], SHORT_TEN)
    dv01 = SHORT_TEN / 100 * r10["dv01"]
    out = {"dv01_2": r2["dv01"], "dv01_10": r10["dv01"], "long_two": long_two, "dv01": dv01}
    for day, (d2, d10) in MOVES.items():
        first = steepener_pnl(dv01, d2, d10)
        full = (long_two / 100 * (TWO.dirty_price(0.0471 + d2 / 1e4, SETTLE) - TWO.dirty_price(0.0471, SETTLE))
                - SHORT_TEN / 100 * (TEN.dirty_price(0.0496 + d10 / 1e4, SETTLE) - TEN.dirty_price(0.0496, SETTLE)))
        out[f"first_{day}"], out[f"full_{day}"] = first, full
    return out


def surprise_regression(n: int = 200, seed: int = 31) -> dict[str, float]:
    """Synthetic: standardised surprises move the 2-year by 8 bp and the 10-year by 5 bp per unit,
    with noise of 3 bp; the regression recovers the sensitivities."""
    rng = random.Random(seed)
    z = [rng.gauss(0, 1) for _ in range(n)]
    d2 = [8 * x + rng.gauss(0, 3) for x in z]
    d10 = [5 * x + rng.gauss(0, 3) for x in z]
    b2, s2 = sensitivity(z, d2)
    b10, s10 = sensitivity(z, d10)
    return {"b2": b2, "se2": s2, "b10": b10, "se10": s10, "z": z, "d2": d2}
