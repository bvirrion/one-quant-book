"""One Quant Book 10, chapter 18: smart order routing -- sweeping five venues against a fast liquidity provider who
fades its quotes, and allocating a passive order across venues.

    VENUES                         five venues A-E: the router's one-way latency to each (it sits next to A), the
                                   fast provider's latency from A (microwave), take and make fees
    race()                         the timeline of a spray and of the fast provider's cancels, from the latencies
    trial(sync, jitter, seed, qty, fees_first, fade)   one sweep in firm.exchsim: each venue shows 200 shares of
                                   slow liquidity and 300 of the fast provider's at 100.01 and 1,000 at 100.02; the
                                   router takes `qty` at 100.01 (spray or synchronised), then cleans up at 100.02;
                                   returns fills at 100.01 by venue, the fill ratio, the fee-adjusted cost per share
    sweep_study()                  spray and synchronised sweeps of the whole level over router jitters, 100 trials
                                   each: fill ratio and fee-adjusted cost; venue fill ratios and the router's ranking
    partial_study()                a 1,000-share buy: venues chosen by fee or by distance, spray or synchronised
    passive_study()                Cont and Kukanov's allocation of a 1,000-share passive buy over four lit venues and
                                   a dark one against simple rules, out of sample
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("sor", "exchsim"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_exchsim import (  # noqa: E402
    SEC,
    ExchangeConfig,
    FeeSchedule,
    LatencyModel,
    Order,
    Phases,
    SessionSpec,
    Simulator,
)
from firm_sor import Fader, Router, Venue, VenueStats, ck_allocate, ck_cost, sweep  # noqa: E402

T0 = 34_200 * SEC
US = 1_000
#            name, router latency (us), fast provider's latency from A (us), take, make
VENUES = (("A", 50, 5, 0.0030, -0.0020), ("B", 120, 45, 0.0030, -0.0025), ("C", 200, 95, 0.0010, 0.0005),
          ("D", 280, 145, 0.0030, -0.0020), ("E", 360, 195, -0.0010, 0.0020))
ASK, ASK2 = 1_000_100, 1_000_200                     # 100.01, 100.02
SLOW, FAST, DEEP = 200, 300, 1_000


def race() -> list:
    """(venue, spray arrival, the fast provider's cancel arrival after a fill at A, synchronised arrival) in us."""
    far = max(r for _, r, *_ in VENUES)
    first = VENUES[0][1] + VENUES[0][2]                  # the fill at A reaches the provider
    return [(n, r, first + m if n != "A" else None, far) for n, r, m, _, _ in VENUES]


def venues() -> list:
    return [Venue(n, r * US, take, make) for n, r, _, take, make in VENUES]


def trial(sync: bool, jitter: float, seed: int, qty: int | None = None, fees_first: bool = True,
          fade: bool = True) -> dict:
    ph = Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=T0 + SEC, end_ns=T0 + SEC + 1)
    sim = Simulator([ExchangeConfig(venue=n, phases=ph, fees=FeeSchedule(make=mk, take=tk))
                     for n, _, _, tk, mk in VENUES], seed=seed)
    ev = []
    for n, *_ in VENUES:
        ev += [(T0 + US, n, Order(side="S", qty=SLOW, price=ASK)), (T0 + US, n, Order(side="S", qty=DEEP, price=ASK2)),
               (T0 + US, n, Order(side="B", qty=DEEP, price=ASK - 100))]
    sim.add_events(orders=ev)
    names = [n for n, *_ in VENUES]
    if fade:
        sim.add_agent(Fader(ASK, FAST, names, T0 + 2 * US),
                      [SessionSpec(venue=n, firm="HFT", cod=False, latency=LatencyModel(m * US, m * US, m * US))
                       for n, _, m, _, _ in VENUES])
    shown = SLOW + (FAST if fade else 0)
    fees = {n: tk for n, _, _, tk, _ in VENUES}
    quotes = [(n, ASK, shown) for n in names]
    if not fees_first:                                   # nearest first
        quotes = sorted(quotes, key=lambda q: dict((n, r) for n, r, *_ in VENUES)[q[0]])
    legs = sweep(quotes, qty or shown * len(names), fees if fees_first else None)
    router = Router(legs, venues(), T0 + 10 * US * 1000, sync, cleanup={n: DEEP for n in names})
    sim.add_agent(router, [SessionSpec(venue=n, firm="RTR", latency=LatencyModel(r * US, r * US, r * US, jitter=jitter))
                           for n, r, *_ in VENUES])
    res = sim.run()
    fills = res.agents["router"].fills
    want = sum(q for _, _, q in legs)
    by = {n: sum(f[5] for f in fills if f[4] == ASK and names[f[1]] == n) for n in names}
    fee = {i: tk for i, (_, _, _, tk, _) in enumerate(VENUES)}
    paid = sum(f[5] * (f[4] / 10_000 + fee[f[1]]) for f in fills)
    got = sum(f[5] for f in fills)
    return {"by_venue": by, "first": sum(by.values()), "want": want, "ratio": sum(by.values()) / want,
            "cost": 100 * (paid / got - ASK / 10_000), "done": got, "sent": {v: q for v, _, q in legs}}


JITTERS = (0.0, 0.05, 0.1, 0.2, 0.4)


@functools.cache
def sweep_study(trials: int = 100) -> dict:
    """Spray and synchronised sweeps of the whole level (2,500 shares) over router latency jitters."""
    out = {}
    stats = {False: VenueStats(), True: VenueStats()}
    for jit in JITTERS:
        for sync in (False, True):
            rows = [trial(sync, jit, 500 + i) for i in range(trials)]
            ratio = np.array([r["ratio"] for r in rows])
            cost = np.array([r["cost"] for r in rows])
            out[(jit, sync)] = {"ratio": float(ratio.mean()), "ratio_sd": float(ratio.std(ddof=1)),
                                "full": float((ratio == 1.0).mean()), "cost": float(cost.mean()),
                                "cost_se": float(cost.std(ddof=1) / math.sqrt(trials))}
            if jit == 0.1:
                for r in rows:
                    for v, q in r["sent"].items():
                        stats[sync].add(v, q, r["by_venue"][v])
    fees = {n: tk for n, _, _, tk, _ in VENUES}
    names = [n for n, *_ in VENUES]
    for sync in (False, True):
        out[("venues", sync)] = {v: stats[sync].fill_ratio(v, (0.0, 0.0)) for v in names}
        out[("rank", sync)] = stats[sync].rank(names, fees)
    return out


@functools.cache
def partial_study(trials: int = 50, jitter: float = 0.1) -> dict:
    """A 1,000-share buy at 100.01: the router picks venues by fee (lowest take fee first) or by distance
    (nearest first), and sprays or synchronises."""
    out = {}
    for fees_first in (True, False):
        for sync in (False, True):
            rows = [trial(sync, jitter, 900 + i, qty=1000, fees_first=fees_first) for i in range(trials)]
            out[(fees_first, sync)] = {"ratio": float(np.mean([r["ratio"] for r in rows])),
                                       "cost": float(np.mean([r["cost"] for r in rows])),
                                       "venues": tuple(rows[0]["sent"])}
    return out


# -- passive allocation (Cont and Kukanov) -----------------------------------------------------------------------------
X_PASSIVE, H, TAKE = 1000, 0.005, 0.0030
LIT = ("A", "B", "C", "D", "dark")
QUEUES = (1500, 2500, 300, 800, 0)
OUTFLOW = (2000, 2200, 900, 1000, 400)            # mean shares leaving the front of each queue in the minute
REBATES = (0.0020, 0.0025, -0.0005, 0.0020, 0.0)
IMPROVE = (0.0, 0.0, 0.0, 0.0, -H)                # the dark venue fills at the mid: half a spread less than the bid
LAM_U, LAM_O = 0.012, 0.012


def outflow(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    common = rng.normal(0.0, 0.4, (n, 1))
    own = rng.normal(0.0, 0.5, (n, len(LIT)))
    return np.asarray(OUTFLOW, float) * np.exp(common + own - 0.5 * (0.4**2 + 0.5**2))


def _evaluate(m, lim, xi, lam_o):
    c, got = ck_cost(m, lim, X_PASSIVE, QUEUES, xi, H, TAKE, REBATES, LAM_U, lam_o, IMPROVE)
    se = 100 * c.std(ddof=1) / X_PASSIVE / math.sqrt(len(c))
    return {"cost": float(100 * c.mean() / X_PASSIVE), "cost_se": float(se),
            "filled": float(np.minimum(got, X_PASSIVE).mean() / X_PASSIVE), "alloc": (float(m), *map(float, lim))}


@functools.cache
def passive_study(train: int = 400, test: int = 20_000, lam_o: float = LAM_O) -> dict:
    xi_train, xi_test = outflow(train, 1), outflow(test, 2)
    k = len(LIT)
    cap = np.maximum(xi_train - np.asarray(QUEUES, float), 0).mean(axis=0)
    rules = {"market order": (X_PASSIVE, np.zeros(k)),
             "highest rebate": (0.0, np.eye(k)[1] * X_PASSIVE),
             "shortest queue": (0.0, np.eye(k)[4] * X_PASSIVE),
             "proportional": (0.0, X_PASSIVE * cap / cap.sum())}
    m, lim = ck_allocate(X_PASSIVE, QUEUES, xi_train, H, TAKE, REBATES, LAM_U, lam_o, IMPROVE)
    rules["Cont-Kukanov"] = (m, lim)
    m2, lim2 = ck_allocate(X_PASSIVE, QUEUES[:4], xi_train[:, :4], H, TAKE, REBATES[:4], LAM_U, lam_o, IMPROVE[:4])
    rules["Cont-Kukanov, no dark"] = (m2, np.r_[lim2, 0.0])
    return {name: _evaluate(mm, ll, xi_test, lam_o) for name, (mm, ll) in rules.items()}
