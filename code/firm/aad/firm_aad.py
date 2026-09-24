"""firm.aad -- algorithmic differentiation for the miniature firm (One Quant Book 4, chapter 28).

Python reference of the firm's AD library (the C++20 header cpp/firm_aad.hpp and the Rust crate are the production
versions, used by the pricing library and risk engine of later books):

    Tape, Var       reverse (adjoint) mode by operator overloading: every elementary operation records its inputs and
                    its local partial derivatives; one reverse sweep accumulates all adjoints
    Dual            forward mode: value and one tangent, carried together
    gradient(f, x)  -> (value, gradient, stats) by one recording and one reverse sweep
    forward_gradient(f, x) -> gradient by n forward-mode passes
    bump_gradient(f, x, h, central) -> finite differences
    checkpointed_gradient(step, x0, theta, n_steps, loss, every) -> reverse mode through a long loop storing only
                    every `every`-th state and recomputing the segments
    ops: exp, log, sqrt, ncdf (standard normal distribution function), maximum
Cost accounting (deterministic): an evaluation performs E elementary operations; the reverse mode performs E operations,
P local partials and P adjoint multiply-adds, where P counts the (operation, input) pairs.
"""
from __future__ import annotations

import math


class Tape:
    def __init__(self) -> None:
        self.parents: list[tuple] = []
        self.partials: list[tuple] = []

    def var(self, value: float) -> Var:
        self.parents.append(())
        self.partials.append(())
        return Var(self, len(self.parents) - 1, float(value))

    def record(self, value: float, parents: tuple, partials: tuple) -> Var:
        self.parents.append(parents)
        self.partials.append(partials)
        return Var(self, len(self.parents) - 1, value)

    def adjoints(self, out: Var) -> list[float]:
        """The reverse sweep: bar(v_j) = sum over the operations i using v_j of bar(v_i) * d v_i / d v_j."""
        bar = [0.0] * len(self.parents)
        bar[out.idx] = 1.0
        for i in range(out.idx, -1, -1):
            b = bar[i]
            if b == 0.0:
                continue
            for p, d in zip(self.parents[i], self.partials[i], strict=True):
                bar[p] += b * d
        return bar

    def stats(self) -> dict:
        n_inputs = sum(1 for p in self.parents if not p)
        ops = len(self.parents) - n_inputs
        return {"ops": ops, "partials": sum(len(p) for p in self.parents), "nodes": len(self.parents)}


def _v(x):
    return x.val if isinstance(x, Var) else float(x)


class Var:
    __slots__ = ("tape", "idx", "val")

    def __init__(self, tape: Tape, idx: int, val: float) -> None:
        self.tape, self.idx, self.val = tape, idx, val

    def _bin(self, other, value, d_self, d_other):
        if isinstance(other, Var):
            return self.tape.record(value, (self.idx, other.idx), (d_self, d_other))
        return self.tape.record(value, (self.idx,), (d_self,))

    def __add__(self, o):
        return self._bin(o, self.val + _v(o), 1.0, 1.0)

    __radd__ = __add__

    def __sub__(self, o):
        return self._bin(o, self.val - _v(o), 1.0, -1.0)

    def __rsub__(self, o):
        return self.tape.record(_v(o) - self.val, (self.idx,), (-1.0,))

    def __mul__(self, o):
        return self._bin(o, self.val * _v(o), _v(o), self.val)

    __rmul__ = __mul__

    def __truediv__(self, o):
        ov = _v(o)
        return self._bin(o, self.val / ov, 1.0 / ov, -self.val / (ov * ov))

    def __rtruediv__(self, o):
        return self.tape.record(_v(o) / self.val, (self.idx,), (-_v(o) / (self.val * self.val),))

    def __neg__(self):
        return self.tape.record(-self.val, (self.idx,), (-1.0,))


class Dual:
    """Forward mode: a value and its derivative along one direction."""

    __slots__ = ("val", "dot")

    def __init__(self, val: float, dot: float = 0.0) -> None:
        self.val, self.dot = float(val), float(dot)

    def __add__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.val + o.val, self.dot + o.dot)

    __radd__ = __add__

    def __sub__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.val - o.val, self.dot - o.dot)

    def __rsub__(self, o):
        return Dual(o) - self

    def __mul__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.val * o.val, self.dot * o.val + self.val * o.dot)

    __rmul__ = __mul__

    def __truediv__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.val / o.val, (self.dot * o.val - self.val * o.dot) / (o.val * o.val))

    def __rtruediv__(self, o):
        return Dual(o) / self

    def __neg__(self):
        return Dual(-self.val, -self.dot)


def _unary(x, f, df):
    if isinstance(x, Var):
        return x.tape.record(f(x.val), (x.idx,), (df(x.val),))
    if isinstance(x, Dual):
        return Dual(f(x.val), df(x.val) * x.dot)
    return f(float(x))


def exp(x):
    return _unary(x, math.exp, math.exp)


def log(x):
    return _unary(x, math.log, lambda v: 1.0 / v)


def sqrt(x):
    return _unary(x, math.sqrt, lambda v: 0.5 / math.sqrt(v))


def ncdf(x):
    """Standard normal distribution function; its derivative is the density."""
    return _unary(x, lambda v: 0.5 * math.erfc(-v / math.sqrt(2)),
                  lambda v: math.exp(-0.5 * v * v) / math.sqrt(2 * math.pi))


def maximum(x, c: float):
    """max(x, c) for a constant c; the derivative at the kink is taken as zero."""
    return _unary(x, lambda v: max(v, c), lambda v: 1.0 if v > c else 0.0)


def gradient(f, x) -> tuple:
    """Value, gradient and operation counts of a scalar function by one recording and one reverse sweep."""
    tape = Tape()
    xs = [tape.var(v) for v in x]
    y = f(xs)
    bar = tape.adjoints(y)
    return y.val, [bar[v.idx] for v in xs], tape.stats()


def forward_gradient(f, x) -> list[float]:
    """n forward-mode passes, one per input direction."""
    out = []
    for i in range(len(x)):
        y = f([Dual(v, 1.0 if j == i else 0.0) for j, v in enumerate(x)])
        out.append(y.dot)
    return out


def bump_gradient(f, x, h: float = 1e-6, central: bool = True) -> list[float]:
    x = [float(v) for v in x]
    base = None if central else f(x)
    g = []
    for i in range(len(x)):
        up = x.copy()
        up[i] += h
        if central:
            dn = x.copy()
            dn[i] -= h
            g.append((f(up) - f(dn)) / (2 * h))
        else:
            g.append((f(up) - base) / h)
    return g


def checkpointed_gradient(step, x0: float, theta: float, n_steps: int, loss, every: int) -> dict:
    """d loss(x_n) / d(x0, theta) for x_{k+1} = step(x_k, theta), keeping only every `every`-th state in memory and
    recomputing each segment on a fresh tape during the reverse pass. Returns the gradient and the peak number of
    states held (checkpoints plus one segment's tape states)."""
    checkpoints = {0: float(x0)}
    x = float(x0)
    for k in range(n_steps):
        x = step(x, theta)
        if (k + 1) % every == 0:
            checkpoints[k + 1] = x
    tape = Tape()
    xv = tape.var(x)
    lo = loss(xv)
    x_bar = tape.adjoints(lo)[xv.idx]
    theta_bar = 0.0
    starts = sorted(k for k in checkpoints if k < n_steps)
    peak = len(checkpoints)
    for s in reversed(starts):
        end = min(s + every, n_steps)
        tape = Tape()
        xs, th = tape.var(checkpoints[s]), tape.var(theta)
        y = xs
        for _ in range(s, end):
            y = step(y, th)
        peak = max(peak, len(checkpoints) + (end - s))
        seed = tape.record(y.val * x_bar, (y.idx,), (x_bar,))    # d(x_bar * y) = x_bar dy
        bar = tape.adjoints(seed)
        x_bar, theta_bar = bar[xs.idx], theta_bar + bar[th.idx]
    return {"d_x0": x_bar, "d_theta": theta_bar, "value": _v(lo), "peak_states": peak}
