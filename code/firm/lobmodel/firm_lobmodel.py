"""firm.lobmodel -- an order-book model end to end, on Book 10's exchange simulator (Book 12, chapter 29).

Sessions come from firm.exchsim with Book 7's firm_tape flow as background. One agent class does both jobs: in
research it records what its feed shows (book tops and trades, as firm.featstore events) and never trades; in
production it computes the same features online with firm.featstore's engine at every change of the top of book,
asks a model for the next second's mid change, declares its decision time with ctx.compute (the model's measured
inference latency plus any other delay), and quotes: one lot at the touch on each side its position allows, except
the side the forecast says is about to be run over, with a timer that flattens a position held too long. Labels come
from firm.labeling, validation from firm.cvsplit's purged folds, the model from firm.gbdt (a TCN from firm.lobseq as
the challenger), its compiled form from firm.mlinfer (C++20 and Rust serving path in cpp/ and rust/, parity vectors
in data/), and the whole run is one firm.workflow graph. report() gives a session's net P&L, the mark-outs of its
entries (firm.markout) and the staleness of its decisions.

API (stable):
    FEATURES ; HORIZON ; open_ns
    ModelAgent(predict, threshold, hold_s, decision_ns, qty, trade) : firm.exchsim Agent; .ev, .decisions, .staleness
    run_session(seed, seconds, agent, latency) -> firm.exchsim Result
    events_array(agent) -> dict of arrays ; dataset(events, times, horizon) -> (X, y, t0, t1)
    report(res, agent, horizons) -> dict(pnl, fees, entries, fills, timeouts, markout {horizon: ticks}, position,
        staleness ms (median), staleness p90 ms)
    ForestPredictor(forest) ; record(seed, seconds) ; stage_data, stage_cv, stage_fit, stage_tcn, stage_threshold,
        stage_test ; trade(forest, seed, seconds, threshold, decision_ns) ; make_pipeline(cache_dir, cfg) ; DEFAULT
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("exchsim", "tape", "featstore", "labeling", "markout", "cvsplit", "gbdt", "mlinfer", "lobseq", "workflow"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_exchsim import (  # noqa: E402
    OPEN_NS,
    SEC,
    Agent,
    ExchangeConfig,
    LatencyModel,
    Order,
    SessionSpec,
    Simulator,
    TapeBackground,
)
from firm_featstore import FeatureDef, OnlineEngine, offline  # noqa: E402
from firm_labeling import fixed_horizon  # noqa: E402
from firm_markout import markouts  # noqa: E402
from firm_mlinfer import read_forest  # noqa: E402,F401  (re-exported for the serving fixture)
from firm_tape import TapeConfig  # noqa: E402

TICK = 100                                                          # price units (1/10,000) per tick
HORIZON = 1.0                                                       # seconds
FEATURES = (FeatureDef("imbalance", "imbalance", "last"), FeatureDef("spread", "spread", "last"),
            FeatureDef("OFI 1 s", "ofi", "sum", 1), FeatureDef("OFI 5 s", "ofi", "sum", 5),
            FeatureDef("signed volume 1 s", "trade_sign", "sum", 1),
            FeatureDef("signed volume 5 s", "trade_sign", "sum", 5), FeatureDef("trades 5 s", "is_trade", "sum", 5),
            FeatureDef("mid change 1 s", "mid", "change", 1), FeatureDef("mid change 5 s", "mid", "change", 5),
            FeatureDef("updates 1 s", "one", "sum", 1))
INPUTS = ("t", "mid", "spread", "imbalance", "ofi", "trade_sign", "is_trade", "one")


class ModelAgent(Agent):
    """Records its feed as events and, with a model, trades on it (see the module docstring)."""

    name = "model"

    def __init__(self, predict=None, threshold=1.0, hold_s=30.0, decision_ns=0, qty=100, trade=True):
        self.predict, self.threshold, self.hold_ns = predict, threshold, int(hold_s * SEC)
        self.decision_ns, self.qty, self.trade = int(decision_ns), qty, trade and predict is not None
        self.ev = {k: [] for k in INPUTS}
        self.engine = OnlineEngine(FEATURES)
        self.sides, self.prev, self.decisions = {}, None, []
        self.live, self.exit_armed, self.timeouts = {}, False, 0
        self.last_ts, self.staleness = 0, []

    def _event(self, t, mid, spread, imb, ofi, sign, trade):
        for k, v in zip(INPUTS, (t, mid, spread, imb, ofi, sign, float(trade), 1.0), strict=True):
            self.ev[k].append(v)
        self.engine.on(len(self.ev["t"]) - 1, self.ev)

    def on_feed(self, ctx, msg):
        k = type(msg).__name__[-1]
        self.last_ts = msg.ts
        if k == "A":
            self.sides[msg.ref] = 1 if msg.side == "B" else -1
        elif k in "EC" and self.prev is not None:
            sign = -self.sides.get(msg.ref, 0)                       # the aggressor is opposite the resting order
            t = (ctx.now_ns - OPEN_NS) / SEC
            self._event(t, self.ev["mid"][-1], self.ev["spread"][-1], self.ev["imbalance"][-1], 0.0,
                        sign * msg.shares / 100.0, 1)

    def on_book(self, ctx, locate, top):
        b, bq, a, aq = top
        if b is None or a is None or a <= b:
            return
        t = (ctx.now_ns - OPEN_NS) / SEC
        ofi = 0.0
        if self.prev is not None:
            pb, pbq, pa, paq = self.prev
            ofi = ((bq if b >= pb else 0) - (pbq if b <= pb else 0) - (aq if a <= pa else 0)
                   + (paq if a >= pa else 0)) / 100.0
        self.prev = top
        self._event(t, (a + b) / (2 * TICK), (a - b) / TICK, (bq - aq) / (bq + aq), ofi, 0.0, 0)
        if not self.trade:
            return
        x = self.engine.values(t)
        f = float(self.predict(x))
        ctx.compute(self.decision_ns)
        self.decisions.append((t, f))
        self.staleness.append(ctx.now_ns + self.decision_ns - self.last_ts)      # exchange event to order departure
        self._act(ctx, f, b, a)

    def _act(self, ctx, f, b, a):
        """Quote one lot at the touch on each side the position allows, except the side the forecast says is about to
        be run over (bid withdrawn when f <= -threshold, ask when f >= threshold); keep a quote whose price is still
        the touch (its queue place is worth keeping), move one that is not."""
        pos = ctx.position(1)
        want = {"B": b if pos < self.qty and f > -self.threshold else None,
                "S": a if pos > -self.qty and f < self.threshold else None}
        have = {"B": False, "S": False}
        for cl, (side, px) in list(self.live.items()):
            if want[side] == px and not have[side]:
                have[side] = True
                continue
            ctx.cancel(cl)
            del self.live[cl]
        for side in ("B", "S"):
            if want[side] is not None and not have[side] and a - b == TICK:
                cl = ctx.send(Order(1, side, self.qty, want[side], post_only=True))
                self.live[cl] = (side, want[side])

    def on_report(self, ctx, rep):
        k = type(rep).__name__[-1]
        if k == "J" or (k == "E" and rep.leaves == 0):
            self.live.pop(rep.cl_ord_id, None)
        if k == "E" and ctx.position(1) != 0 and not self.exit_armed:
            self.exit_armed = True
            ctx.set_timer(self.hold_ns, ctx.position(1))
        if ctx.position(1) == 0:
            self.exit_armed = False

    def on_timer(self, ctx, tag):
        """A position still open after the holding period is flattened at the market."""
        p = ctx.position(1)
        if p and p == tag:
            for cl in list(self.live):
                ctx.cancel(cl)
            self.live.clear()
            ctx.send(Order(1, "S" if p > 0 else "B", abs(p), 0, tif="I"))
            self.timeouts += 1
        self.exit_armed = False


def run_session(seed, seconds, agent, latency=None):
    """One session: SIMX with default fees (make -0.002, take 0.003 per share), the firm_tape background of this
    seed, the agent behind Book 10's latency model (20 microseconds each way by default)."""
    sim = Simulator(ExchangeConfig(), seed=seed)
    sim.add_background(TapeBackground(TapeConfig(seconds=seconds, seed=seed, news_at=None)))
    sim.add_agent(agent, SessionSpec(firm="ML1", latency=latency or LatencyModel()))
    return sim.run()


def events_array(agent):
    return {k: np.asarray(v, dtype=float) for k, v in agent.ev.items()}


def dataset(ev, times, horizon=HORIZON):
    """Features at the decision times (firm.featstore offline) and the fixed-horizon label of firm.labeling in event
    time: the mid change (ticks) from the last event known at the decision to the last one `horizon` seconds later,
    with each label's span (t0, t1) for purged validation."""
    X = offline(ev, FEATURES, times)
    t = ev["t"]
    k0 = np.searchsorted(t, times, side="right") - 1
    k1 = np.searchsorted(t, times + horizon, side="right") - 1
    r = np.r_[0.0, np.diff(ev["mid"])]                                 # per-event mid changes
    y = fixed_horizon(r, k0, k1 - k0)["ret"]
    return X, y, times, times + horizon


def report(res, agent, horizons=(0.1, 1.0, 5.0)):
    """Net P&L in currency (cash with fees, the position marked at the last mid), entries and their mark-outs: for each
    fill that opens a position, side x (market mid h seconds later - fill price), in ticks, mean over entries."""
    ctx = res.agents[agent.name]
    tp = res.tape()
    top = tp.top
    ok = (top["bid"] > 0) & (top["ask"] > top["bid"])
    mt, mid = top["t"][ok], 0.5 * (top["bid"] + top["ask"])[ok].astype(float)          # ticks
    pnl = ctx.cash + ctx.position(1) * mid[-1] * TICK / 10_000.0
    pos, entries = 0, []
    for ts, _v, _loc, sign, px, qty, liq, _fee in ctx.fills:
        if pos == 0:
            entries.append(((ts - OPEN_NS) / SEC, sign, px / TICK, liq))
        pos += sign * qty
    e = np.array([(t, sg, px) for t, sg, px, _ in entries]) if entries else np.zeros((0, 3))
    M = markouts(e[:, 0], e[:, 1], e[:, 2], mt, mid, np.asarray(horizons)) if len(e) else None
    mo = {h: float(M[:, j].mean()) if M is not None else float("nan") for j, h in enumerate(horizons)}
    st = np.asarray(agent.staleness, dtype=float) / 1e6
    return {"pnl": float(pnl), "fees": float(ctx.fees), "entries": len(entries), "fills": len(ctx.fills),
            "timeouts": agent.timeouts, "markout": mo, "position": ctx.position(1),
            "staleness ms": float(np.median(st)) if len(st) else float("nan"),
            "staleness p90 ms": float(np.quantile(st, 0.9)) if len(st) else float("nan")}


# ---------------------------------------------------------------------------------------------------- serving
class ForestPredictor:
    """firm.mlinfer's flat forest walked for all trees at once (NumPy over trees, a loop over depth); the leaf values
    are then added tree by tree in order, as forest_predict and the C++ and Rust kernels do, so that all four agree
    bit for bit."""

    def __init__(self, f):
        self.f = {k: np.asarray(v) for k, v in f.items()}

    def __call__(self, x):
        f, n = self.f, self.f["roots"].astype(np.int64)
        while True:
            inner = n >= 0
            if not inner.any():
                break
            m = n[inner]
            go = np.asarray(x)[f["feature"][m]] <= f["threshold"][m]
            n[inner] = np.where(go, f["left"][m], f["right"][m])
        s = 0.0
        for v in f["value"][-n - 1].tolist():
            s += v
        return s


# ---------------------------------------------------------------------------------------------------- the pipeline
def record(seed, seconds):
    """A research session: the recorder's events and the decision times (its book updates, after the longest window
    and before the last horizon)."""
    a = ModelAgent(trade=False)
    run_session(seed, seconds, a)
    ev = events_array(a)
    book = ev["t"][ev["is_trade"] == 0]
    return ev, book[(book >= 5.0) & (book <= seconds - HORIZON)]


def stage_data(inputs, params, seed):
    """Features and labels for a list of session seeds, each session's times shifted so that sessions follow one
    another (for purged folds)."""
    Xs, ys, t0s, t1s, ss = [], [], [], [], []
    for i, s in enumerate(params["seeds"]):
        ev, times = record(s, params["seconds"])
        X, y, t0, t1 = dataset(ev, times)
        off = i * (params["seconds"] + 10.0)
        Xs.append(X)
        ys.append(y)
        t0s.append(t0 + off)
        t1s.append(t1 + off)
        ss.append(np.full(len(y), i))
    return {"X": np.vstack(Xs), "y": np.concatenate(ys), "t0": np.concatenate(t0s), "t1": np.concatenate(t1s),
            "session": np.concatenate(ss)}


def ic(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def stage_cv(inputs, params, seed):
    """Purged five-fold cross-validation (firm.cvsplit, one-second embargo) of each LightGBM configuration on the
    training sessions; the mean fold IC of each, and the chosen one."""
    from firm_cvsplit import PurgedKFold
    from firm_gbdt import make

    d = inputs["train"]
    cv = PurgedKFold(d["t0"], d["t1"], n_splits=5, embargo=1.0)
    scores = []
    for cfg in params["grid"]:
        s = [ic(make(cfg, seed=seed).fit(d["X"][tr], d["y"][tr]).predict(d["X"][te]), d["y"][te])
             for tr, te in cv.split(d["X"])]
        scores.append(float(np.mean(s)))
    return {"scores": scores, "chosen": params["grid"][int(np.argmax(scores))]}


def stage_fit(inputs, params, seed):
    """The chosen configuration refitted on all training sessions, exported to flat arrays (firm.mlinfer), with its
    validation IC and parity vectors (validation rows and LightGBM's own predictions)."""
    from firm_gbdt import make
    from firm_mlinfer import export_forest, forest_predict

    d, v = inputs["train"], inputs["valid"]
    model = make(inputs["cv"]["chosen"], seed=seed).fit(d["X"], d["y"])
    f = export_forest(model)
    V = v["X"][:: max(1, len(v["X"]) // 200)][:200]
    return {"forest": f, "valid ic": ic(model.predict(v["X"]), v["y"]), "train ic": ic(model.predict(d["X"]), d["y"]),
            "vectors": V, "lightgbm": model.predict(V), "flat": forest_predict(f, V)}


def trade(forest, seed, seconds, threshold, decision_ns, predict=None):
    a = ModelAgent(predict or ForestPredictor(forest), threshold, decision_ns=decision_ns)
    return report(run_session(seed, seconds, a), a)


def _windows(d, T):
    """Sequences of the last T decisions' features within each session, with the label of the last one."""
    idx = [i for i in range(len(d["y"])) if i >= T - 1 and d["session"][i - T + 1] == d["session"][i]]
    idx = np.array(idx)
    X = np.stack([d["X"][i - T + 1:i + 1] for i in idx]).astype(np.float32)
    return X, d["y"][idx]


def stage_tcn(inputs, params, seed):
    """Chapter 8's small TCN (firm.lobseq) on windows of the last T decisions: trained on all training sessions but
    the last, stopped early on the last, scored by IC on the validation sessions."""
    import torch
    from firm_lobseq import TCN, Scaler, evaluate, train

    torch.set_num_threads(1)
    d, v, T = inputs["train"], inputs["valid"], params["T"]
    X, y = _windows(d, T)
    last = d["session"].max()
    keep = np.array([d["session"][i] for i in range(len(d["y"])) if i >= T - 1
                     and d["session"][i - T + 1] == d["session"][i]]) != last
    sc = Scaler().fit(X[keep])
    cls = lambda r: (np.sign(r) + 1).astype(int)                    # noqa: E731  down, flat, up
    torch.manual_seed(seed)
    model = TCN(X.shape[-1])
    model, _, best = train(model, sc.transform(X[keep]), cls(y[keep]), sc.transform(X[~keep]), cls(y[~keep]),
                           epochs=params["epochs"], seed=seed)
    Xv, yv = _windows(v, T)
    return {"valid ic": evaluate(model, sc.transform(Xv), cls(yv), yv)["ic"], "best epoch": best,
            "parameters": int(sum(p.numel() for p in model.parameters()))}


def stage_threshold(inputs, params, seed):
    """Mean validation-session P&L of each forecast threshold at the compiled model's decision time; the best one."""
    f = inputs["fit"]["forest"]
    pnl = [float(np.mean([trade(f, s, params["seconds"], th, params["decision_ns"])["pnl"] for s in params["seeds"]]))
           for th in params["grid"]]
    return {"pnl": pnl, "chosen": params["grid"][int(np.argmax(pnl))]}


def stage_test(inputs, params, seed):
    """On the test sessions: the model at each decision latency, and the same quoting without a model."""
    f, th = inputs["fit"]["forest"], inputs["threshold"]["chosen"]
    out = {"latency ns": list(params["latencies"]), "model": [], "no model": []}
    for lat in params["latencies"]:
        out["model"].append([trade(f, s, params["seconds"], th, lat) for s in params["seeds"]])
    out["no model"] = [trade(f, s, params["seconds"], np.inf, 0) for s in params["seeds"]]
    return out


def make_pipeline(cache_dir, cfg):
    """The whole chapter as one firm.workflow graph (cfg: seeds, seconds, grids, latencies)."""
    from firm_workflow import Pipeline, Stage

    return Pipeline([
        Stage("train", stage_data, (), {"seeds": cfg["train"], "seconds": cfg["seconds"]}),
        Stage("valid", stage_data, (), {"seeds": cfg["valid"], "seconds": cfg["seconds"]}),
        Stage("cv", stage_cv, ("train",), {"grid": cfg["grid"]}, 1),
        Stage("fit", stage_fit, ("train", "valid", "cv"), {}, 1),
        Stage("tcn", stage_tcn, ("train", "valid"), {"T": cfg["T"], "epochs": cfg["epochs"]}, 1),
        Stage("threshold", stage_threshold, ("fit",), {"seeds": cfg["valid"], "seconds": cfg["seconds"],
                                                      "grid": cfg["thresholds"], "decision_ns": cfg["decision_ns"]}),
        Stage("test", stage_test, ("fit", "threshold"), {"seeds": cfg["test"], "seconds": cfg["seconds"],
                                                        "latencies": cfg["latencies"]}),
    ], cache_dir)


GRID = tuple({"n_estimators": 150, "num_leaves": nl, "learning_rate": 0.05, "min_child_samples": 200}
             for nl in (7, 15, 31))
DEFAULT = {"train": tuple(range(1000, 1008)), "valid": (2000, 2001, 2002), "test": (3000, 3001, 3002, 3003, 3004, 3005),
           "seconds": 1200.0, "grid": GRID, "T": 16, "epochs": 8, "thresholds": (0.05, 0.1, 0.15, 0.2),
           "decision_ns": 150,                                           # the C++ branches, measured (chapter 29)
           "latencies": (0, 150, 263_000, 1_000_000, 10_000_000, 30_000_000, 50_000_000, 70_000_000, 100_000_000,
                         150_000_000)}
