"""One Quant Book 10, chapter 16: benchmark algorithms, intraday volume forecasts, and what forecast errors cost.

    panel(seed)                        simulated intraday volumes: STOCKS stocks x DAYS days x BINS bins, a U-shaped
                                       profile per stock, a market factor (daily and intraday), a stock-specific AR(1)
                                       deviation within the day, and news days whose volume surges from a random bin
    forecast_study()                   the forecasters (static curve, rolling average, rolling + AR tilt, PCA-ARMA
                                       static and dynamic) on the test days: error of the day's volume shares and the
                                       VWAP tracking error (the schedule part of the slippage) on all days and on
                                       high-volume days
    activity(), flow()                 the panel as firm.agentmkt activity curves, and the volume the simulator prints
                                       for each stock-day (its noise takers' orders, drawn in advance from the seed)
    Slicer                             the execution agent: at the start of each bin it asks its schedule for the
                                       bin's quantity (the schedule sees the market's and its own volume so far) and
                                       sends it as four market orders over the bin; it counts the market's volume from
                                       the public feed; an optional market-on-close order
    run, day_stats, fills              one simulated day (optionally with a closing auction) and its measurements
    vwap_study()                       static and dynamic VWAP on 16 high-volume and 16 normal stock-days (same flow):
                                       the slippage against the day's VWAP split into its schedule and execution parts
    pov_study()                        a participation algorithm, and two at once, on a normal and a thin day
    benchmark_study()                  VWAP, TWAP, POV, implementation shortfall and close on the same days, each
                                       against its benchmark, the arrival price and the day without it
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("algos", "acexec", "agentmkt", "auctionsim", "exchsim"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import SEC, T0, Population, PopulationConfig, session  # noqa: E402
from firm_algos import PCAARMA, LevelAR, Profile, close, decompose, profile, shortfall, tracking, vwap  # noqa: E402
from firm_auctionsim import final_cross  # noqa: E402
from firm_exchsim import Agent, ExchangeConfig, Order, Phases  # noqa: E402

STOCKS, DAYS, BINS = 20, 250, 26
BIN_S = 60.0                            # the simulated day: 26 bins of one minute
DAY_S = BINS * BIN_S
TRAIN, WINDOW = 60, 20                  # the static curve is fitted once on the first 60 days; rolling windows of 20
DAILY_VOL = 0.02
NEWS_P = 0.08


def base_shape(bins: int = BINS) -> np.ndarray:
    x = np.linspace(-1.0, 1.0, bins)
    s = 1.0 + 1.5 * x**2
    s[-1] *= 1.6                                                       # the run-up to the close
    return s / s.sum()


@functools.cache
def panel(seed: int = 16, news_p: float = NEWS_P) -> dict:
    rng = np.random.default_rng(seed)
    shape = base_shape() * np.exp(0.1 * rng.standard_normal((STOCKS, BINS)))
    shape /= shape.sum(axis=1, keepdims=True)
    level = np.exp(rng.normal(np.log(1e6), 0.5, STOCKS))
    f = np.zeros(DAYS)
    for d in range(1, DAYS):
        f[d] = 0.6 * f[d - 1] + 0.15 * rng.standard_normal()
    m = np.zeros((DAYS, BINS))                                          # market intraday deviation
    e = np.zeros((STOCKS, DAYS, BINS))                                  # stock-specific intraday deviation
    m[:, 0] = 0.15 / math.sqrt(1 - 0.25) * rng.standard_normal(DAYS)
    e[:, :, 0] = 0.25 / math.sqrt(1 - 0.49) * rng.standard_normal((STOCKS, DAYS))
    for k in range(1, BINS):
        m[:, k] = 0.5 * m[:, k - 1] + 0.15 * rng.standard_normal(DAYS)
        e[:, :, k] = 0.7 * e[:, :, k - 1] + 0.25 * rng.standard_normal((STOCKS, DAYS))
    news = rng.random((STOCKS, DAYS)) < news_p
    k0 = rng.integers(2, BINS - 4, (STOCKS, DAYS))
    amp = rng.uniform(1.0, 2.0, (STOCKS, DAYS))
    k = np.arange(BINS)
    surge = np.where(k[None, None, :] >= k0[..., None], amp[..., None] * np.exp(-(k - k0[..., None]) / 4.0), 0.0)
    surge *= news[..., None]
    u = 0.2 * rng.standard_normal((STOCKS, DAYS))
    v = (level[:, None, None] * np.exp(f[None, :, None] + u[..., None]) * shape[:, None, :]
         * np.exp(m[None] + e + surge))
    return {"v": v, "news": news, "shape": shape}


def market(curve=()) -> PopulationConfig:
    return PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10, fund=0.05, v_rate=0.2,
                            curve=tuple(float(x) for x in curve))


def _high(v: np.ndarray, d: int) -> np.ndarray:
    """Stocks whose day-d volume is more than 1.5 times their mean daily volume over the previous WINDOW days."""
    return v[:, d].sum(axis=1) > 1.5 * v[:, d - WINDOW:d].sum(axis=2).mean(axis=1)


NAMES = ("static curve", "rolling", "level + AR dynamic", "PCA-ARMA", "PCA-ARMA dynamic")


@functools.cache
def activity(seed: int = 16, news_p: float = NEWS_P) -> np.ndarray:
    """The panel scaled so that each stock's mean bin is one: the simulator's activity curves."""
    v = panel(seed, news_p)["v"]
    return v / v.mean(axis=(1, 2), keepdims=True)


def day_seed(j: int, d: int) -> int:
    return 100_000 + 1000 * j + d


@functools.cache
def flow(seed: int = 16, news_p: float = NEWS_P) -> np.ndarray:
    """The simulator's printed noise-taker volume per bin (shares) for every stock-day: firm.agentmkt draws these
    orders in advance, so they are known without running the market, and a run with the same seed prints them."""
    a = activity(seed, news_p)
    out = np.zeros((STOCKS, DAYS, BINS))
    for j in range(STOCKS):
        for d in range(DAYS):
            ex = Population(market(a[j, d]), day_seed(j, d), DAY_S).exo
            t = np.array([x[0] for x in ex if x[1] == "noise"])
            q = np.array([abs(x[2]) for x in ex if x[1] == "noise"], float)
            out[j, d] = np.bincount(np.minimum((t / BIN_S).astype(int), BINS - 1), weights=q, minlength=BINS)
    return out


@functools.cache
def forecast_study(seed: int = 16, news_p: float = NEWS_P) -> dict:
    v = flow(seed, news_p)
    sigma_bin = DAILY_VOL / math.sqrt(BINS) * 1e4                      # basis points a bin
    static = [profile(v[j, :TRAIN]) for j in range(STOCKS)]
    err = {n: [] for n in NAMES}
    trk = {n: [] for n in NAMES}
    high = []
    for d in range(TRAIN, DAYS):
        hi = _high(v, d)
        adv = v[:, d - WINDOW:d].sum(axis=2).mean(axis=1)
        turn = v[:, d - WINDOW:d] / adv[:, None, None]                  # turnover: volume over the stock's mean day
        fit = PCAARMA(np.transpose(turn, (1, 2, 0)))
        for j in range(STOCKS):
            day = v[j, d]
            share = day / day.sum()
            roll = profile(v[j, d - WINDOW:d])
            models = {"static curve": (Profile(static[j], adv[j]), False),
                      "rolling": (Profile(roll, adv[j]), False),
                      "level + AR dynamic": (LevelAR.fit(v[j, d - WINDOW:d]), True),
                      "PCA-ARMA": (fit.model(j), False),
                      "PCA-ARMA dynamic": (fit.model(j), True)}
            for n, (mod, dyn) in models.items():
                obs = day / adv[j] if n.startswith("PCA") else day
                q = vwap(1.0, mod, obs, dyn)
                err[n].append(float(np.abs(q - share).sum()))
                trk[n].append(sigma_bin * math.sqrt(tracking(q, day)))
            high.append(bool(hi[j]))
    high = np.array(high)
    out = {"high_share": float(high.mean()), "n": int(len(high)), "n_high": int(high.sum())}
    for n in NAMES:
        t = np.array(trk[n])
        out[n] = {"l1": float(np.mean(err[n])), "all": float(np.sqrt(np.mean(t**2))),
                  "normal": float(np.sqrt(np.mean(t[~high] ** 2))), "high": float(np.sqrt(np.mean(t[high] ** 2)))}
    return out


# -- the algorithms in the simulated market -------------------------------------------------------------------------
CHILDREN = 4
QTY = 15_000


class Slicer(Agent):
    """At the start of each bin, schedule(k, total, own, planned) gives the bin's quantity: total and own are the
    market's and the agent's volumes in bins 0..k-1 (the market's counted from the public feed), planned what was
    planned for them. The bin's quantity goes out as CHILDREN market orders spread over the bin, each topping the
    fills up to the plan so far; an optional
    market-on-close order (moc = (seconds before the close, shares)) joins the closing auction."""

    def __init__(self, schedule, side: str = "B", name: str = "algo", moc=None):
        self.schedule, self.side, self.name, self.moc = schedule, side, name, moc
        self.vol, self.own, self.plan = np.zeros(BINS), np.zeros(BINS), np.zeros(BINS)
        self.filled = 0

    def _bin(self, ctx) -> int:
        return min(int((ctx.now_ns - T0) / SEC / BIN_S), BINS - 1)

    def on_start(self, ctx):
        for k in range(BINS):
            for i in range(CHILDREN):
                ctx.set_timer(int((k * BIN_S + i * BIN_S / CHILDREN) * SEC) + T0 - ctx.now_ns, (k, i))
        if self.moc:
            ctx.set_timer(T0 + int((DAY_S - self.moc[0]) * SEC) - ctx.now_ns, "moc")

    def on_feed(self, ctx, m):
        if type(m).__name__ in ("Feed_E", "Feed_C") and ctx.now_ns >= T0:
            self.vol[self._bin(ctx)] += m.shares

    def on_report(self, ctx, rep):
        if type(rep).__name__ == "Out_E" and ctx.now_ns >= T0:
            self.own[self._bin(ctx)] += rep.qty
            self.filled += rep.qty

    def on_timer(self, ctx, tag):
        if tag == "moc":
            ctx.send(Order(side=self.side, qty=int(self.moc[1]), price=0, tif="C"))
            return
        k, i = tag
        if i == 0:                         # the bin's quantity, from what is known now
            q = self.schedule(k, self.vol[:k].copy(), self.own[:k].copy(),
                              self.plan[:k].sum())
            self.plan[k] = max(0.0, float(q))
        target = self.plan[:k].sum() + self.plan[k] * (i + 1) / CHILDREN
        q = int(round((target - self.filled) / 100)) * 100   # what the fills leave to do
        if q > 0:
            ctx.send(Order(side=self.side, qty=q, price=0, tif="I"))


def _bins(t_s, x, w=None):
    k = np.clip((np.asarray(t_s) / BIN_S).astype(int), 0, BINS - 1)
    x = np.asarray(x, float)
    return np.bincount(k, weights=x if w is None else x * np.asarray(w, float), minlength=BINS)


def run(curve, agents, seed: int, close: bool = False):
    end = T0 + int(DAY_S * SEC)
    venue = None
    if close:
        venue = ExchangeConfig(phases=Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 60 * SEC,
                                             close_auction=True))
    res, _ = session(market(curve), DAY_S, seed, agents=list(agents), venue=venue)
    return res


def day_stats(res) -> dict:
    """The day's continuous trading per bin (volumes, VWAPs, in ticks), the mids, and the closing cross if any."""
    tp = res.tape()
    tr = tp.trades[tp.trades["t"] < DAY_S]
    v = _bins(tr["t"], tr["qty"])
    w = _bins(tr["t"], tr["qty"], tr["price"]) / np.maximum(v, 1)
    top = tp.top
    ok = (top["bid"] > 0) & (top["ask"] > 0) & (top["t"] < DAY_S)
    tt, mid = top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok])
    grid = (np.arange(BINS) + 0.5) * BIN_S
    mids = mid[np.maximum(np.searchsorted(tt, grid, side="right") - 1, 0)]
    fc = final_cross(res)
    return {"v": v, "w": w, "arrival": float(mid[max(np.searchsorted(tt, 0.0, side="right") - 1, 0)]),
            "twap": float(mids.mean()), "end_mid": float(mid[-1]), "close": fc[1] / 100 if fc else None,
            "vwap": float(v @ w / v.sum()), "tt": tt, "mid": mid}


def fills(res, name: str) -> dict:
    f = res.agents[name].fills
    t = np.array([(x[0] - T0) / SEC for x in f])
    q = np.array([x[5] for x in f], float)
    p = np.array([x[4] for x in f], float) / 100.0
    cont = t < DAY_S
    qb = _bins(t[cont], q[cont])
    return {"t": t, "q": q, "p": p, "qb": qb, "fb": _bins(t[cont], q[cont], p[cont]) / np.maximum(qb, 1),
            "avg": float(q @ p / q.sum()), "done": float(q.sum())}


# -- VWAP on the simulator's days --------------------------------------------------------------------------------------
def _days(n_each: int, seed: int = 16) -> tuple[list, list]:
    """The first n_each high-volume stock-days of the test period, and n_each normal ones spread across it."""
    v = flow(seed)
    high, normal = [], []
    for d in range(TRAIN, DAYS):
        hi = _high(v, d)
        for j in range(STOCKS):
            (high if hi[j] else normal).append((j, d))
    return high[:n_each], normal[:: len(normal) // n_each][:n_each]


def example_days(seed: int = 16) -> tuple:
    """An ordinary day and a news day of the same stock, for the chapter's first figure."""
    pn = panel(seed)
    j = 0
    news = [d for d in range(TRAIN, DAYS) if pn["news"][j, d] and _high(flow(seed), d)[j]]
    normal = [d for d in range(TRAIN, DAYS) if not pn["news"][j, d] and not _high(flow(seed), d)[j]]
    return (j, normal[0]), (j, news[0])


def vwap_schedules(j: int, d: int, seed: int = 16):
    """The static and dynamic VWAP schedules for stock j's day d, from its last WINDOW days of printed volume; the
    dynamic one follows the other traders' volume (the market's minus its own)."""
    hist = flow(seed)[j, d - WINDOW:d]
    static, dyn = Profile(profile(hist), hist.sum(axis=1).mean()), LevelAR.fit(hist)

    def static_schedule(k, total, own, planned):
        f = static.remaining(np.zeros(0))
        return QTY * f[k] / f.sum()

    def dynamic_schedule(k, total, own, planned):
        f = dyn.remaining(total - own)
        return (QTY - planned) * f[0] / f.sum()
    return static_schedule, dynamic_schedule


def vwap_day(j: int, d: int, dynamic: bool, seed: int = 16) -> dict:
    sch = vwap_schedules(j, d, seed)[int(dynamic)]
    res = run(activity(seed)[j, d], [Slicer(sch)], day_seed(j, d))
    st, fl = day_stats(res), fills(res, "algo")
    ex, sc = decompose(fl["qb"], fl["fb"], st["v"], st["w"])
    return {"exec": ex, "sched": sc, "total": ex + sc, "done": fl["done"],
            "tracking": tracking(fl["qb"], st["v"]), "check": fl["avg"] - st["vwap"],
            "part": fl["done"] / st["v"].sum()}


@functools.cache
def vwap_study(n_each: int = 16, seed: int = 16) -> dict:
    high, normal = _days(n_each, seed)
    out = {}
    for label, days in (("high", high), ("normal", normal)):
        for dyn in (False, True):
            a = np.array([[r["total"], r["sched"], r["exec"], r["done"], r["part"], r["check"]]
                          for r in (vwap_day(j, d, dyn, seed) for j, d in days)])
            out[(label, "dynamic" if dyn else "static")] = {
                "rms": float(np.sqrt(np.mean(a[:, 0] ** 2))), "mean": float(a[:, 0].mean()),
                "sd": float(a[:, 0].std(ddof=1)), "sched_sd": float(a[:, 1].std(ddof=1)),
                "exec_mean": float(a[:, 2].mean()), "exec_sd": float(a[:, 2].std(ddof=1)),
                "explained": float(1 - a[:, 2].var(ddof=1) / a[:, 0].var(ddof=1)), "done": float(a[:, 3].min()),
                "part": float(a[:, 4].mean()), "identity": float(np.abs(a[:, 5] - a[:, 0]).max()), "rows": a}
        st, dy = out[(label, "static")]["rows"][:, 0], out[(label, "dynamic")]["rows"][:, 0]
        x = st**2 - dy**2
        out[(label, "paired")] = {"mean": float(x.mean()), "se": float(x.std(ddof=1) / math.sqrt(len(x))),
                                  "better": int(np.sum(np.abs(dy) < np.abs(st)))}
    return out


# -- participation and its feedback -----------------------------------------------------------------------------------
RATE = 0.2


def pov_schedule(rate: float, qty: float = QTY):
    """Trade in bin k to be `rate` of the market: rate x bin k-1's whole volume, the algorithm's own included."""
    def schedule(k, total, own, planned):
        if k == 0:
            return 0.0
        return min(qty - planned, rate * total[k - 1])
    return schedule


def typical_curve(scale: float = 1.0, seed: int = 16) -> tuple:
    return tuple(scale * activity(seed)[0].mean(axis=0))


@functools.cache
def pov_study(seeds=tuple(range(1, 9)), rate: float = RATE) -> dict:
    """One POV buyer of QTY, and two at once, on a normal and a thin (0.4) day, against the same day without them
    (common random numbers): share done, minutes to finish, participation (own over total volume), pace (own over
    the volume the day had without them), the others' extra volume per share the algorithms bought, and the impact
    cost (fills against the mid the same day had without them)."""
    out = {}
    for label, scale in (("normal", 1.0), ("thin", 0.4)):
        curve = typical_curve(scale)
        rows = {k: [] for k in ("one", "two")}
        for s in seeds:
            base = day_stats(run(curve, [], 500 + s))
            for kind in rows:
                ags = [Slicer(pov_schedule(rate), name="algo")]
                if kind == "two":
                    ags.append(Slicer(pov_schedule(rate), name="b"))
                res = run(curve, ags, 500 + s)
                st, fl = day_stats(res), fills(res, "algo")
                own_all = sum(fills(res, a.name)["qb"] for a in ags)
                last = int(np.nonzero(fl["qb"])[0].max())
                win = slice(1, last + 1)
                others = st["v"][win].sum() - own_all[win].sum()
                cf = base["mid"][np.maximum(np.searchsorted(base["tt"], fl["t"], side="right") - 1, 0)]
                rows[kind].append((fl["done"] / QTY, last + 1, fl["qb"][win].sum() / st["v"][win].sum(),
                                   fl["qb"][win].sum() / base["v"][win].sum(),
                                   (others - base["v"][win].sum()) / own_all[win].sum(),
                                   fl["avg"] - float(fl["q"] @ cf / fl["q"].sum())))
        for kind, x in rows.items():
            a = np.array(x)
            n = math.sqrt(len(a))
            out[(label, kind)] = {"done": float(a[:, 0].mean()), "minutes": float(a[:, 1].mean()),
                                  "part": float(a[:, 2].mean()), "pace": float(a[:, 3].mean()),
                                  "induced": float(a[:, 4].mean()), "induced_se": float(a[:, 4].std(ddof=1) / n),
                                  "cost": float(a[:, 5].mean()), "cost_se": float(a[:, 5].std(ddof=1) / n)}
    return out


# -- the five algorithms against their benchmarks -------------------------------------------------------------------
KT_IS = 4.0
CLOSE_START, MOC_SHARE = 17, 0.3


def five(seed: int = 16) -> dict:
    """The five schedules for a buy of QTY on stock 0's typical day (static forecasts from its typical profile)."""
    prof = Profile(np.array(typical_curve(1.0, seed)), 1.0)
    f = prof.remaining(np.zeros(0))
    is_q = shortfall(QTY, BINS, KT_IS)
    close_q, moc = close(QTY, prof, MOC_SHARE, CLOSE_START)
    return {"VWAP": (lambda k, *_: QTY * f[k] / f.sum(), None),
            "TWAP": (lambda k, *_: QTY / BINS, None),
            "POV": (pov_schedule(0.1), None),
            "IS": (lambda k, *_: is_q[k], None),
            "close": (lambda k, *_: close_q[k], (30.0, moc))}


@functools.cache
def benchmark_study(seeds=tuple(range(1, 9))) -> dict:
    """Each algorithm on the same days, against its own benchmark and against the arrival price (ticks per share,
    positive = paid more), what its buying did to the benchmark, and its impact cost: the fills against the mid the
    same day had without it (common random numbers)."""
    curve = typical_curve()
    rows = {n: [] for n in five()}
    for s in seeds:
        base = day_stats(run(curve, [], 700 + s, close=True))
        for name, (sch, moc) in five().items():
            res = run(curve, [Slicer(sch, moc=moc)], 700 + s, close=True)
            st, fl = day_stats(res), fills(res, "algo")
            if name == "VWAP":
                bench, b0 = st["vwap"], base["vwap"]
            elif name == "TWAP":
                bench, b0 = st["twap"], base["twap"]
            elif name == "POV":
                last = int(np.nonzero(fl["qb"])[0].max())
                bench = float(st["v"][: last + 1] @ st["w"][: last + 1] / st["v"][: last + 1].sum())
                b0 = float(base["v"][: last + 1] @ base["w"][: last + 1] / base["v"][: last + 1].sum())
            elif name == "IS":
                bench, b0 = st["arrival"], base["arrival"]
            else:
                bench, b0 = st["close"], base["close"] or base["end_mid"]
            cf = base["mid"][np.maximum(np.searchsorted(base["tt"], fl["t"], side="right") - 1, 0)]
            cf[fl["t"] >= DAY_S] = b0 if name == "close" else base["end_mid"]
            rows[name].append((fl["avg"] - bench, fl["avg"] - st["arrival"], bench - b0, fl["done"],
                               fl["avg"] - float(fl["q"] @ cf / fl["q"].sum())))
    out = {}
    for name, x in rows.items():
        a = np.array(x)
        n = math.sqrt(len(a))
        out[name] = {"bench": float(a[:, 0].mean()), "bench_sd": float(a[:, 0].std(ddof=1)),
                     "arrival": float(a[:, 1].mean()), "arrival_sd": float(a[:, 1].std(ddof=1)),
                     "arrival_se": float(a[:, 1].std(ddof=1) / n), "moved": float(a[:, 2].mean()),
                     "done": float(a[:, 3].min()), "impact": float(a[:, 4].mean()),
                     "impact_se": float(a[:, 4].std(ddof=1) / n)}
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(forecast_study(), indent=1))
