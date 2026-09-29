"""Signal serving and parameter management (One Quant Book 15, chapter 16).

Ten quoting strategies (chapter 11's, one lot a side) each trade one hour of Book 10's simulator on its own firm.tape
session. Their inventory limit is a parameter: a share of the strategy's capital, intended as 50 basis points (two
lots); typed as 50 into an untyped store and read as 50 percent, it becomes two hundred lots. The change is planted ten
minutes into the session. A monitor compares each five-minute fill count with the strategy's usual count for that
window and fires above 1.3 times. Three policies are compared: the change to every strategy at once, a staged rollout
(one canary strategy for thirty minutes, then the rest), and a typed parameter store whose schema refuses the entry.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/paramstore", "code/firm/btengine", "code/platforms/11-backtest-engine-architecture/python"):
    sys.path.insert(0, str(ROOT / p))
import firm_btengine as B  # noqa: E402
import firm_paramstore as S  # noqa: E402
from pl_btengine import Quoter  # noqa: E402

CAPITAL, PRICE, LOT = 4e6, 100.0, 100          # dollars, dollars per share, shares per lot
T0, WINDOW, STAGE = 600.0, 300.0, 1800.0       # change at 10 minutes; five-minute windows; canary for 30 minutes
RATIO = 1.3                                    # the fill-rate monitor's threshold
CAP_SHARES = 300                               # the most the intended limit ever holds (two lots and a pending one)
SEEDS = tuple(range(1, 11))
SCHEMA = S.Schema("inventory_limit", "fraction", {"bp": 1e-4, "percent": 1e-2, "fraction": 1.0},
                  lo=0.0, hi=0.02, max_step=0.005, two_approvals_above=0.002)


def lots(fraction: float) -> int:
    return int(round(fraction * CAPITAL / PRICE / LOT))


class Limited(Quoter):
    """The quoter with its limit read from a schedule: `before` lots, then `after` lots from time `t0`."""

    def __init__(self, before: int, after: int, t0: float):
        super().__init__(limit=before)
        self.before, self.after, self.t0 = LOT * before, LOT * after, t0

    def on_market(self, ctx, t, snap):
        self.limit = self.after if t >= self.t0 else self.before
        super().on_market(ctx, t, snap)


def run(seed: int, after: int, seconds: float = 3600.0, t0: float = T0, data=None) -> dict:
    data = data or B.DataAccess(tempfile.mkdtemp())
    name = data.tape(seconds, seed)
    r = B.Engine(4, Limited(lots(0.005), after, t0), data, {"dataset": name, "latency": 20e-6, "seed": 1}).run()
    f = r.fills
    return {"t": f[:, 0], "pos": np.cumsum(f[:, 1] * f[:, 2]), "seconds": seconds}


def windows(r: dict) -> np.ndarray:
    return np.histogram(r["t"], bins=np.arange(0.0, r["seconds"] + 1, WINDOW))[0]


def detection(base: dict, wrong: dict, start: float) -> float | None:
    """End of the first window after `start` whose fills exceed RATIO times the usual count."""
    b, w = windows(base), windows(wrong)
    for k in range(len(w)):
        if k * WINDOW >= start and w[k] > RATIO * max(b[k], 1):
            return (k + 1) * WINDOW
    return None


def excess_path(wrong: dict, grid: np.ndarray, start: float, stop: float) -> np.ndarray:
    """Dollars of inventory beyond what the intended limit allows, on a time grid, between start and stop."""
    idx = np.searchsorted(wrong["t"], grid, side="right") - 1
    pos = np.where(idx >= 0, wrong["pos"][np.maximum(idx, 0)], 0.0)
    ex = np.maximum(np.abs(pos) - CAP_SHARES, 0.0) * PRICE
    return np.where((grid >= start) & (grid < stop), ex, 0.0)


def incident(seeds=SEEDS, seconds: float = 3600.0) -> dict:
    data = B.DataAccess(tempfile.mkdtemp())
    wrong_lots = lots(0.5)                                    # 50 read as percent
    runs = {s: (run(s, lots(0.005), seconds, data=data), run(s, wrong_lots, seconds, data=data)) for s in seeds}
    det = {s: detection(b, w, T0) for s, (b, w) in runs.items()}
    grid = np.arange(0.0, seconds + 1, 10.0)
    end = seconds
    # all at once: every strategy from T0 until the first detection, then rolled back everywhere
    t_all = min((d for d in det.values() if d is not None), default=end)
    path_all = sum(excess_path(w, grid, T0, t_all) for _b, w in runs.values())
    # staged: the canary (first seed) alone until T0 + STAGE; the rest only if the canary has not fired
    canary = seeds[0]
    t_can = det[canary]
    if t_can is not None and t_can <= T0 + STAGE:
        t_staged, path_staged = t_can, excess_path(runs[canary][1], grid, T0, t_can)
    else:
        rest = {s: detection(runs[s][0], runs[s][1], T0 + STAGE) for s in seeds[1:]}
        t_staged = min([d for d in rest.values() if d is not None] + ([t_can] if t_can else []), default=end)
        path_staged = excess_path(runs[canary][1], grid, T0, t_staged) + sum(
            excess_path(runs[s][1], grid, T0 + STAGE, t_staged) for s in seeds[1:])
    minutes = lambda p: float(p.sum() * 10.0 / 60.0)          # dollar-minutes on a 10-second grid  # noqa: E731
    return {"grid": grid, "detection": det, "wrong_lots": wrong_lots,
            "all": {"detect_min": (t_all - T0) / 60, "peak": float(path_all.max()), "dollar_min": minutes(path_all),
                    "path": path_all},
            "staged": {"detect_min": (t_staged - T0) / 60, "peak": float(path_staged.max()),
                       "dollar_min": minutes(path_staged), "path": path_staged},
            "schema": {"detect_min": 0.0, "peak": 0.0, "dollar_min": 0.0, "path": 0 * grid}}


def governance(root: pathlib.Path) -> dict:
    """The store's side of the story: the units error refused, a legitimate change approved, flags, history, drift."""
    store = S.ParamStore(root)
    store.register(SCHEMA)
    day = 24 * 3600.0
    first = store.propose("q01", "inventory_limit", 50, "bp", 0.0, 0.0, "ana")
    store.approve(first.cid, "ben", 0.0)
    no_unit = store.propose("q01", "inventory_limit", 50, "", 5 * day + 37800, 5 * day + 37800, "ana")
    percent = store.propose("q01", "inventory_limit", 50, "percent", 5 * day + 37800, 5 * day + 37800, "ana")
    raise_ = store.propose("q01", "inventory_limit", 75, "bp", 7 * day + 36000, 7 * day + 35000, "ana")
    store.approve(raise_.cid, "ana", 7 * day + 35100)                         # the author cannot approve
    store.approve(raise_.cid, "ben", 7 * day + 35200)
    after_one = raise_.status
    store.approve(raise_.cid, "cleo", 7 * day + 35300)
    # a correction recorded on day 9, effective from day 7 10:30: what was live at 10:31 depends on when you ask
    fix = store.propose("q01", "inventory_limit", 60, "bp", 7 * day + 37800, 9 * day, "ben")
    store.approve(fix.cid, "cleo", 9 * day + 60)
    t = 7 * day + 37860                                                       # day 7, 10:31
    flags = S.Flags()
    flags.set("limit-75bp", ["q01"])
    declared = {f"q{i:02d}": {"inventory_limit": 0.005} for i in range(1, 4)}
    running = {"q01": {"inventory_limit": 0.005}, "q02": {"inventory_limit": 0.5}, "q03": {"inventory_limit": 0.005}}
    return {"no_unit": no_unit.reasons, "percent": percent.reasons, "raise_needed": raise_.needed,
            "after_one": after_one, "raise_status": raise_.status, "raise_approvals": raise_.approvals,
            "live_as_known_day8": store.as_of("q01", "inventory_limit", t, 8 * day),
            "live_as_known_now": store.as_of("q01", "inventory_limit", t),
            "flag_q01": flags.on("limit-75bp", "q01"), "flag_q02": flags.on("limit-75bp", "q02"),
            "drift": S.drift(declared, running), "audit_ok": store.audit.verify() == -1,
            "history": store.history("q01", "inventory_limit")}


def signals() -> list[tuple]:
    svc = S.SignalService(max_age=300.0, fallback=0.0)
    svc.publish("momentum_20d", 0.8, "v3", 0.0)
    svc.publish("momentum_20d", 0.7, "v3", 60.0)
    return [(now, *svc.get("momentum_20d", now)) for now in (30.0, 200.0, 600.0)] + [(0.0, *svc.get("x", 0.0))]
