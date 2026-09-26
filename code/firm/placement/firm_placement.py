"""firm.placement -- child-order placement: a Markov model of the best quotes, its dynamic-programming solution, a
tabular Q-learning baseline, and a slice executor for the simulated market (build of One Quant Book 10, chapter 17).

The placement problem: buy r lots (sell: the mirror image) within a horizon, with a one-tick spread. A resting buy
order sits behind n lots at the bid; the ask queue holds A lots. In a small step dt one event happens at most: a
market sell (rate mu, one lot) takes the front of the bid (one lot of ours when n = 0, at half a tick below the
mid), a lot ahead of us cancels (rate theta n), the ask shrinks (rate mu + theta A; when it empties the price moves up
one tick and the remaining lots start again from a fresh queue, one tick worse), or grows (rate lam). Crossing buys
the remaining lots at the ask (half a tick above the mid for the first A lots, 1.5 for the next depth2, 2.5 beyond).
Costs are in ticks against the mid at the start, summed over lots.

API (stable):
    BookModel(lam, theta, mu, fresh, depth2)   rates per second (lots), fresh = law of a best queue's size (1, 2, ...)
    calibrate(res, venue="")                   a BookModel from a firm.exchsim Result's feed (time-weighted)
    cross_cost(r, a, depth2)                   ticks for crossing r lots against an ask of a lots
    solve(model, r_max, horizon_s, dt, n_max, a_max) -> Plan: .cross[k][r, n, a] (cross now with k steps left?),
                                               .value(r, n, a) at the start, .fresh_value[k][r]
    Plan.decide(r, n, a, seconds_left)         True to cross now
    imbalance_threshold(plan, r, k)            (I*, agreement): the rule "cross at once if (B - A) / (B + A) > I*"
                                               closest to the plan's decision with k steps left (default: all)
    qlearn(model, r_max, horizon_s, dt, episodes, seed) -> Q table over (r, n, a, time bucket, action)
    simulate(model, policy, r, horizon_s, dt, paths, seed)  Monte Carlo cost of a policy(r, n, a, k) -> cross?
    SliceExecutor(slices, policy, check_s)     a firm.exchsim Agent: each slice (start_ns, side, qty, horizon_s[,
                                               limit]) is worked by the policy object and cleaned up at its deadline;
                                               an optional limit price caps every order of the slice
    Cross, Post(offset, reprice), Imbalance(threshold, inner), DPPolicy(plan)   the executor's policies
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "exchsim"))
from firm_exchsim import SEC, Agent, Order  # noqa: E402
from firm_lob import MessageBook  # noqa: E402

LOT = 100


@dataclass(frozen=True)
class BookModel:
    lam: float
    theta: float
    mu: float
    fresh: tuple
    depth2: float


def cross_cost(r, a, depth2: float):
    r, a = np.asarray(r, float), np.asarray(a, float)
    first = np.minimum(r, a)
    second = np.minimum(r - first, depth2)
    return 0.5 * first + 1.5 * second + 2.5 * (r - first - second)


def calibrate(res, venue: str = "") -> BookModel:
    """Limit orders joining the best quote, cancellations at the best (per lot), market orders (executions at the
    best), in lots a second per side; the time-weighted law of the best queues' sizes and of the second level."""
    bk = MessageBook()
    lots_t = arr = canc = ex = 0.0
    hist: dict[int, float] = {}
    lvl2 = 0.0
    t_prev = t_first = None
    for ts, _, m in res.feed_messages(venue):
        k = type(m).__name__[-1]
        if k not in "AEXDC" or not getattr(m, "locate", 0):
            continue
        b, bq, a, aq = bk.top()
        if t_prev is not None and b is not None and a is not None:
            dt = (ts - t_prev) / SEC
            lots_t += dt * (bq + aq) / LOT
            for q in (bq // LOT, aq // LOT):
                hist[q] = hist.get(q, 0.0) + dt
            d = bk.depth(-1, 2) + bk.depth(1, 2)
            lvl2 += dt * sum(x[1] for x in (d[1:2] + d[3:4])) / LOT / 2
        if t_first is None and b is not None and a is not None:
            t_first = ts
        t_prev = ts
        if k == "A":
            if (m.side == "B" and m.price == b) or (m.side == "S" and m.price == a):
                arr += m.shares / LOT
            bk.apply("A", m.ref, 1 if m.side == "B" else -1, m.price, m.shares)
            continue
        o = bk.book.get(m.ref)
        at_best = o is not None and o.price in (b, a)
        if k in "EC":
            ex += m.shares / LOT if at_best else 0.0
            bk.apply("X", m.ref, qty=m.shares)
        elif k == "X":
            canc += m.shares / LOT if at_best else 0.0
            bk.apply("X", m.ref, qty=m.shares)
        else:
            canc += o.qty / LOT if at_best else 0.0
            bk.apply("D", m.ref)
    span = (t_prev - t_first) / SEC
    total = sum(hist.values())
    qmax = max(k for k in hist if k > 0)
    fresh = tuple(hist.get(q, 0.0) / (total - hist.get(0, 0.0)) for q in range(1, qmax + 1))
    return BookModel(lam=arr / span / 2, theta=canc / lots_t, mu=ex / span / 2, fresh=fresh,
                     depth2=lvl2 / (t_prev - t_first) * SEC)


class Plan:
    def __init__(self, model, r_max, dt, n_max, a_max, cross, value, fresh_value):
        self.model, self.r_max, self.dt, self.n_max, self.a_max = model, r_max, dt, n_max, a_max
        self.cross, self._value, self.fresh_value = cross, value, fresh_value

    def value(self, r: int, n: int, a: int) -> float:
        return float(self._value[r, min(n, self.n_max), min(a, self.a_max)])

    def decide(self, r: int, n: int, a: int, seconds_left: float) -> bool:
        k = min(int(seconds_left / self.dt), len(self.cross) - 1)
        if k <= 0 or r <= 0:
            return True
        return bool(self.cross[k][min(r, self.r_max), min(n, self.n_max), max(1, min(a, self.a_max))])


def _fresh(model, size: int) -> np.ndarray:
    f = np.zeros(size + 1)
    p = np.asarray(model.fresh, float)[:size]
    f[1:len(p) + 1] = p
    return f / f.sum()


def solve(model: BookModel, r_max: int, horizon_s: float, dt: float = 0.2, n_max: int = 40,
          a_max: int = 40) -> Plan:
    n, a = np.arange(n_max + 1)[:, None], np.arange(a_max + 1)[None, :]
    p_sell = model.mu * dt
    p_canc = model.theta * n * dt
    p_down = (model.mu + model.theta * a) * dt
    p_up = model.lam * dt
    p_none = 1 - p_sell - p_canc - p_down - p_up
    if p_none.min() < 0:
        raise ValueError("dt too large for the rates")
    f = _fresh(model, max(n_max, a_max))
    fb, fa = f[: n_max + 1], f[: a_max + 1]
    cc = [np.broadcast_to(cross_cost(r, a, model.depth2), (n_max + 1, a_max + 1)) for r in range(r_max + 1)]
    v = [c.copy() for c in cc]                                           # k = 0: cross what is left
    w = np.array([float(fa @ cross_cost(r, np.arange(a_max + 1), model.depth2)) for r in range(r_max + 1)])
    steps = int(round(horizon_s / dt))
    crosses, fresh_values = [np.ones((r_max + 1, n_max + 1, a_max + 1), bool)], [w.copy()]
    for _ in range(steps):
        new, flag = [np.zeros_like(v[0])], np.zeros((r_max + 1, n_max + 1, a_max + 1), bool)
        for r in range(1, r_max + 1):
            x = v[r]
            ahead = np.vstack([x[:1] * 0, x[:-1]])               # n - 1
            fill = -0.5 + v[r - 1][0][None, :]                   # our front lot fills
            sell = np.where(n > 0, ahead, fill)
            down = np.hstack([x[:, :1] * 0, x[:, :-1]])          # a - 1
            down[:, 1] = r * 1.0 + w[r]                          # the ask empties: a tick worse
            up = np.hstack([x[:, 1:], x[:, -1:]])
            cont = (p_sell * sell + p_canc * ahead + p_down * down + p_up * up
                    + p_none * x)
            cross = cc[r] <= cont
            new.append(np.where(cross, cc[r], cont))
            flag[r] = cross
        v = new
        w = np.array([0.0] + [float(fb @ v[r] @ fa) for r in range(1, r_max + 1)])
        crosses.append(flag)
        fresh_values.append(w.copy())
    return Plan(model, r_max, dt, n_max, a_max, crosses, np.array(v), fresh_values)


def imbalance_threshold(plan: Plan, r: int, k: int | None = None) -> tuple[float, float]:
    """The single rule "cross at once when (B - A) / (B + A) > I*" closest to the plan's decision with k steps left
    (default: the start), over fresh queues weighted by their law: (I*, share of the weight the rule classifies as
    the plan does). I* = 1 when the plan never crosses."""
    k = len(plan.cross) - 1 if k is None else k
    f = _fresh(plan.model, max(plan.n_max, plan.a_max))
    b, a = np.meshgrid(np.arange(1, plan.n_max + 1), np.arange(1, plan.a_max + 1), indexing="ij")
    w = (f[b] * f[a]).ravel()
    imb = ((b - a) / (b + a)).ravel()
    cross = plan.cross[k][r, 1:, 1:].ravel()
    cuts = np.unique(imb)
    cands = np.r_[(cuts[:-1] + cuts[1:]) / 2, 1.0]
    agree = [float(w @ ((imb > c) == cross)) / w.sum() for c in cands]
    i = len(agree) - 1 - int(np.argmax(agree[::-1]))          # ties: the most patient rule
    return float(cands[i]), agree[i]


def _step(model, rng, n, a, dt, size):
    """One step of the Markov book for arrays of states: returns (event code, uniform) with 0 none, 1 sell,
    2 cancel ahead, 3 ask down, 4 ask up."""
    u = rng.random(size)
    p1 = model.mu * dt
    p2 = p1 + model.theta * n * dt
    p3 = p2 + (model.mu + model.theta * a) * dt
    p4 = p3 + model.lam * dt
    return np.select([u < p1, u < p2, u < p3, u < p4], [1, 2, 3, 4], 0)


def simulate(model: BookModel, policy, r: int, horizon_s: float, dt: float = 0.2, paths: int = 20_000,
             seed: int = 1, n_cap: int = 40, a_cap: int = 40) -> np.ndarray:
    """Cost per path (ticks, summed over lots) of policy(r, n, a, k) -> bool array (cross now), vectorised over paths;
    paths start from fresh queues and join the back of the bid."""
    rng = np.random.default_rng(seed)
    f = _fresh(model, max(n_cap, a_cap))
    steps = int(round(horizon_s / dt))
    rr = np.full(paths, r)
    nn = rng.choice(len(f), paths, p=f)
    aa = rng.choice(len(f), paths, p=f)
    cost = np.zeros(paths)
    live = np.ones(paths, bool)
    for k in range(steps, -1, -1):
        go = live & ((k == 0) | policy(rr, np.minimum(nn, n_cap), np.minimum(aa, a_cap), k))
        cost[go] += cross_cost(rr[go], aa[go], model.depth2)
        live &= ~go
        if k == 0 or not live.any():
            break
        ev = _step(model, rng, nn, aa, dt, paths)
        ev[~live] = 0
        fill = (ev == 1) & (nn == 0)
        cost[fill] -= 0.5
        rr[fill] -= 1
        nn[((ev == 1) & (nn > 0)) | (ev == 2)] -= 1
        aa[ev == 4] += 1
        down = ev == 3
        aa[down] -= 1
        moved = down & (aa == 0)
        cost[moved] += rr[moved]
        nn[moved] = rng.choice(len(f), moved.sum(), p=f)
        aa[moved] = rng.choice(len(f), moved.sum(), p=f)
        live &= rr > 0
    return cost


def qlearn(model: BookModel, r_max: int, horizon_s: float, dt: float = 0.2, episodes: int = 200_000,
           batch: int = 2_000, seed: int = 1, n_cap: int = 20, a_cap: int = 20, bucket_s: float = 5.0,
           eps: float = 0.1, alpha: float = 0.1) -> np.ndarray:
    """Tabular Q-learning of the cross-or-wait decision on the Markov book (costs, so the greedy action is the
    argmin); state (r, n, a, time bucket), capped. Batches of episodes run in lockstep; each step averages the
    targets that land on the same state-action before one update."""
    rng = np.random.default_rng(seed)
    steps = int(round(horizon_s / dt))
    per = max(1, int(round(bucket_s / dt)))
    nb = steps // per + 1
    q = np.zeros((r_max + 1, n_cap + 1, a_cap + 1, nb, 2))
    f = _fresh(model, max(n_cap, a_cap))
    shape = q.shape
    for _ in range(episodes // batch):
        rr = np.full(batch, r_max)
        nn = rng.choice(len(f), batch, p=f)
        aa = rng.choice(len(f), batch, p=f)
        live = np.ones(batch, bool)
        for k in range(steps, 0, -1):
            n_c, a_c, b = np.minimum(nn, n_cap), np.clip(aa, 1, a_cap), k // per
            greedy = np.argmin(q[rr, n_c, a_c, b], axis=1)
            act = np.where(rng.random(batch) < eps, rng.integers(0, 2, batch), greedy)
            cost = np.where(act == 1, cross_cost(rr, aa, model.depth2), 0.0)
            ev = _step(model, rng, nn, aa, dt, batch)
            ev[act == 1] = 0
            r2, n2, a2 = rr.copy(), nn.copy(), aa.copy()
            fill = (ev == 1) & (nn == 0)
            cost = cost - 0.5 * fill
            r2[fill] -= 1
            n2[((ev == 1) & (nn > 0)) | (ev == 2)] -= 1
            a2[ev == 4] += 1
            down = ev == 3
            a2[down] -= 1
            moved = down & (a2 == 0)
            cost = cost + np.where(moved, r2, 0)
            n2[moved] = rng.choice(len(f), moved.sum(), p=f)
            a2[moved] = rng.choice(len(f), moved.sum(), p=f)
            done = (act == 1) | (r2 == 0)
            b2 = (k - 1) // per
            if k - 1 == 0:
                nxt = np.where(done, 0.0, cross_cost(r2, a2, model.depth2))
                done = np.ones(batch, bool)
            else:
                nxt = np.where(done, 0.0, q[r2, np.minimum(n2, n_cap), np.clip(a2, 1, a_cap), b2].min(axis=1))
            target = cost + nxt
            idx = np.ravel_multi_index((rr, n_c, a_c, np.full(batch, b), act), shape)[live]
            s = np.bincount(idx, weights=target[live], minlength=q.size)
            c = np.bincount(idx, minlength=q.size)
            flat = q.reshape(-1)
            hit = c > 0
            flat[hit] += alpha * (s[hit] / c[hit] - flat[hit])
            live &= ~done
            rr, nn, aa = np.where(live, r2, rr), np.where(live, n2, nn), np.where(live, a2, aa)
            if not live.any():
                break
    return q


def q_policy(q: np.ndarray, dt: float = 0.2, bucket_s: float = 5.0):
    per = max(1, int(round(bucket_s / dt)))
    n_cap, a_cap = q.shape[1] - 1, q.shape[2] - 1

    def policy(r, n, a, k):
        z = q[r, np.minimum(n, n_cap), np.clip(a, 1, a_cap), k // per]
        return z[..., 1] < z[..., 0]
    return policy


# -- the executor in the simulated market ------------------------------------------------------------------------------
class Cross:
    def act(self, st):
        return "cross"


class Post:
    """Rest at the best bid (buy) plus `offset` ticks (-1: one behind); with reprice, follow the bid when it moves
    away (the repricing rule), losing the place in the queue."""

    def __init__(self, offset: int = 0, reprice: bool = False):
        self.offset, self.reprice = offset, reprice

    def act(self, st):
        target = st["near"] + st["sign"] * self.offset * st["tick"]
        if st["price"] is None or (self.reprice and st["price"] != target):
            return ("post", target)
        return "wait"


class Imbalance:
    """Cross at once when the queue imbalance on the order's side is above the threshold, else run `inner`."""

    def __init__(self, threshold: float, inner=None):
        self.threshold, self.inner = threshold, inner or Post(0, True)

    def act(self, st):
        if st["first"] and st["imbalance"] > self.threshold:
            return "cross"
        return self.inner.act(st)


class DPPolicy:
    def __init__(self, plan: Plan):
        self.plan = plan

    def act(self, st):
        lots = math.ceil(st["left"] / LOT)
        at_best = st["price"] == st["near"]
        ahead = st["ahead"] if at_best and st["ahead"] is not None else st["near_qty"]
        n = ahead // LOT                # lots ahead: ours, or a place at the back
        if self.plan.decide(lots, n, st["far_qty"] // LOT, st["seconds_left"]):
            return "cross"
        return "wait" if at_best else ("post", st["near"])


class SliceExecutor(Agent):
    """Works slices (start_ns, side, qty, horizon_s) one at a time with a policy; every check_s it builds the state
    (the near and far quotes and sizes, the imbalance on the order's side, the working order's price and the lots
    ahead of it, what is left and the time left) and applies the policy's action: wait, post at a price (cancelling
    the working order), or cross (a marketable order for the rest). At the deadline it cancels and crosses."""

    name = "placer"

    def __init__(self, slices, policy, check_s: float = 1.0, tick: int = 100):
        self.slices, self.policy, self.check, self.tick = slices, policy, check_s, tick
        self.log = []                                      # (slice, t_ns, imbalance at start, arrival mid)
        self.cur = None

    def on_start(self, ctx):
        for i, (t, *_rest) in enumerate(self.slices):
            ctx.set_timer(t - ctx.now_ns, ("start", i))

    def _state(self, ctx, first=False):
        side, qty = self.slices[self.cur][1], self.slices[self.cur][2]
        b, bq, a, aq = ctx.top(1)
        sign = 1 if side == "B" else -1
        near, near_q, far, far_q = (b, bq, a, aq) if side == "B" else (a, aq, b, bq)
        w = [o for o in ctx.working() if o["side"] == side]
        left = qty - self.done
        limit = self.slices[self.cur][4] if len(self.slices[self.cur]) > 4 else None
        return {"limit": limit, "sign": sign, "near": near, "near_qty": near_q, "far": far, "far_qty": far_q,
                "tick": self.tick,
                "imbalance": (near_q - far_q) / max(near_q + far_q, 1), "first": first,
                "price": w[0]["price"] if w else None, "ahead": w[0]["ahead"] if w else None,
                "left": left, "seconds_left": (self.deadline - ctx.now_ns) / SEC, "working": w}

    def _cross(self, ctx, st):
        for o in st["working"]:
            ctx.cancel(o["cl"])
        if st["left"] > 0:
            side = "B" if st["sign"] > 0 else "S"
            px = 0 if st["limit"] is None else int(st["limit"])       # a limit caps the clean-up too
            ctx.send(Order(side=side, qty=int(st["left"]), price=px, tif="I"))
        self.cur = None

    def on_timer(self, ctx, tag):
        if tag[0] == "start":
            if self.cur is not None:                        # the previous slice overran: clean it up first
                self._cross(ctx, self._state(ctx))
            i = tag[1]
            self.cur, self.done, self.deadline = i, 0, ctx.now_ns + int(self.slices[i][3] * SEC)
            st = self._state(ctx, first=True)
            b, _, a, _ = ctx.top(1)
            self.log.append((i, ctx.now_ns, st["imbalance"], 0.5 * (a + b) if a and b else None))
            self._apply(ctx, st)
            ctx.set_timer(int(self.check * SEC), ("check", i))
            return
        i = tag[1]
        if self.cur != i:
            return
        st = self._state(ctx)
        if st["left"] <= 0:
            self.cur = None
            return
        if ctx.now_ns >= self.deadline - int(self.check * SEC / 2):
            self._cross(ctx, st)
            return
        self._apply(ctx, st)
        ctx.set_timer(int(self.check * SEC), ("check", i))

    def _apply(self, ctx, st):
        act = self.policy.act(st)
        if act == "cross":
            self._cross(ctx, st)
        elif act != "wait" and st["near"] is not None:
            for o in st["working"]:
                ctx.cancel(o["cl"])
            side = "B" if st["sign"] > 0 else "S"
            px = int(act[1])
            if st["limit"] is not None:
                px = min(px, int(st["limit"])) if st["sign"] > 0 else max(px, int(st["limit"]))
            ctx.send(Order(side=side, qty=int(st["left"]), price=px))

    def on_report(self, ctx, rep):
        if type(rep).__name__ == "Out_E" and self.cur is not None:
            self.done += rep.qty
