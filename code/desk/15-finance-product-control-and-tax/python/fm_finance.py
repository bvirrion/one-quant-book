"""One Quant Book 16, chapter 15: a day's flash and final P&L, and the tax drag of three strategies (illustrative).

The day: ten instruments held at the start of the day, 40 fills of which those after 16:15 miss the flash, fees on
every fill, and independent price verification of the three least liquid names against a consensus. Prices are in
ledger units (1/10,000 of a dollar), as firm.pnl keeps them.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/signoff"))
import firm_signoff as so  # noqa: E402

U = 10_000                     # ledger units per dollar
SYMS = [f"S{i}" for i in range(10)]
ILLIQUID = ["S7", "S8", "S9"]
SHORTS = ["S3", "S5"]
CUT = 16 * 60 + 15             # flash cut-off, minutes after midnight


def day(seed=18):
    rng = np.random.default_rng(seed)
    sod_px = {s: int(round(rng.uniform(20, 200), 2) * U) for s in SYMS}
    sod = {s: int((-1 if s in SHORTS else 1) * rng.integers(20, 80) * 1000) for s in SYMS}
    move = {s: rng.normal(0.006, 0.01) * (-1 if s in SHORTS else 1) for s in SYMS}
    flash = {s: int(round(sod_px[s] * (1 + move[s]) / 100) * 100) for s in SYMS}
    close = {s: int(round(flash[s] * (1 + rng.normal(0, 0.002 if s not in ILLIQUID else 0.006)) / 100) * 100)
             for s in SYMS}
    consensus = {s: int(round(close[s] * (1 - abs(rng.normal(0.012, 0.004))) / 100) * 100) for s in ILLIQUID}
    tolerance = {s: int(0.005 * close[s]) for s in ILLIQUID}
    fills = []
    for _ in range(40):
        s = SYMS[int(rng.integers(0, 10))]
        t = int(rng.integers(9 * 60 + 30, 17 * 60 + 30))
        side = int(rng.choice([1, -1]))
        q = int(rng.integers(1, 10)) * 1000
        px = int(round(sod_px[s] * (1 + move[s] * (t - 570) / 390 + rng.normal(0, 0.002)) / 100) * 100)
        fills.append((t, s, side, q, px, int(0.0005 * q * px)))
    fills.sort()
    final = so.verified_marks(close, consensus, tolerance)
    return {"sod": sod, "sod_px": sod_px, "flash": flash, "close": close, "final": final, "fills": fills,
            "consensus": consensus, "tolerance": tolerance}


def the_walk(seed=18):
    d = day(seed)
    w = so.walk(d["sod"], d["sod_px"], d["fills"], CUT, d["flash"], d["close"], d["final"])
    return {k: v / U for k, v in w.items()}


def late_count(seed=18):
    return sum(1 for f in day(seed)["fills"] if f[0] > CUT)


SEED = 18
ABS_TOL, REL_TOL = 100_000.0, 0.10
CAT_TOL = {"valuation adjustments": 100_000.0, "late trades": 50_000.0}


def day_exceptions(seed=SEED):
    w = the_walk(seed)
    return so.exceptions(w, ABS_TOL, REL_TOL, CAT_TOL)


def day_signoff(seed=SEED):
    w = the_walk(seed)
    trail = so.Trail()
    trail.add("product control", "18:40", f"flash {w['flash']:.0f} published")
    status = so.sign(trail, "head of product control", "19:30", w, so.exceptions(w, ABS_TOL, REL_TOL, CAT_TOL))
    return status, trail.entries


STRATEGIES = {"statistical arbitrage": (0.12, 40.0, 0.01), "momentum": (0.09, 6.0, 0.015),
              "value": (0.07, 0.8, 0.035)}                       # gross return, turnover, dividend yield
REGIMES = {"no transaction tax, 15% withholding": (0.0, 0.15), "0.5% tax on purchases": (0.005, 0.0),
           "0.2% tax on purchases, 15% withholding": (0.002, 0.15)}   # illustrative inputs


def tax_table():
    return {s: {g: so.tax_drag(r, t, tt, dy, wht) for g, (tt, wht) in REGIMES.items()}
            for s, (r, t, dy) in STRATEGIES.items()}


def half_turnovers(net=0.08, rates=(0.001, 0.002, 0.005)):
    return {tt: so.half_turnover(net, tt) for tt in rates}
