"""firm.payoffdsl -- a payoff scripting language on Book 5's pricing library (build of One Quant Book 15, chapter 19).

A script describes a product's cash flows on named observation schedules; the library supplies the paths, the market,
the discounting and the risk. Grammar (statements end with ';', blocks are braces):

    program   := ('state' NAME '=' expr ';' | 'at' NAME block)*
    block     := '{' stmt* '}'
    stmt      := NAME '=' expr ';' | 'if' expr block ('else' (block | if-stmt))? | 'pay' expr ';' | 'stop' ';'
    expr      := or ; or := and ('or' and)* ; and := not ('and' not)* ; not := 'not' not | cmp
    cmp       := sum (('<'|'<='|'>'|'>='|'=='|'!=') sum)? ; sum := term (('+'|'-') term)*
    term      := unary (('*'|'/') unary)* ; unary := '-' unary | atom
    atom      := NUMBER | NAME | NAME '(' expr (',' expr)* ')' | '(' expr ')'     functions: min, max, abs

At each date of a schedule the block runs with S (the first underlying's spot), perf (the worst performance, spot over
initial fixing) and t (years from the valuation date) defined, the script's parameters as constants and its state
variables as they were left; 'pay x' pays x on that date (discounted on the instrument's curve), 'stop' ends the
product on the path. Blocks on the same date run in script order. Errors carry their line and column.

API (stable):
    parse(text) -> Program ; schedule(program, dates {name: [date]}) -> [(date, block index)] (the event schedule)
    Interpreter(program).run(paths_perf, paths_spot, times, dfs, params) -> pv per path      (loops over paths)
    compile_program(program) -> callable with the same signature                            (arrays over paths)
    ScriptedInstrument(id, underlying, currency, script, dates, params, underlyings, initial, notional=1.0)
    ScriptEngine(n_paths=100_000, mode='compiled'|'interpreted'), registered with firm.pricing for BlackScholes
    ScriptError(message, line, col)
    Quote(value).set(v) ; LazyPrice(compute, *inputs).value       observers: recomputed only when asked and stale
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pricing"))
import firm_pricing as FP  # noqa: E402

KEYWORDS = {"state", "at", "if", "else", "pay", "stop", "and", "or", "not"}
FUNCS = {"min", "max", "abs"}
TOKEN = re.compile(r"\s*(?:(?P<num>\d+\.?\d*(?:[eE][-+]?\d+)?)|(?P<name>[A-Za-z_]\w*)"
                   r"|(?P<op><=|>=|==|!=|[-+*/<>(){};=,])|(?P<comment>#[^\n]*)|(?P<bad>\S))")


class ScriptError(ValueError):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"line {line}, column {col}: {message}")
        self.line, self.col = line, col


@dataclass(frozen=True)
class Tok:
    kind: str
    text: str
    line: int
    col: int


def tokenize(text: str) -> list[Tok]:
    out, pos = [], 0
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if m is None or m.end() == pos:
            break
        start = m.start(m.lastgroup)
        line = text.count("\n", 0, start) + 1
        col = start - (text.rfind("\n", 0, start) + 1) + 1
        kind = m.lastgroup
        if kind == "bad":
            raise ScriptError(f"unexpected character {m.group(kind)!r}", line, col)
        if kind != "comment":
            word = m.group(kind)
            out.append(Tok("kw" if kind == "name" and word in KEYWORDS else kind, word, line, col))
        pos = m.end()
    out.append(Tok("end", "", text.count("\n") + 1, 1))
    return out


# ------------------------------------------------------------ the syntax tree
@dataclass(frozen=True)
class Num:
    value: float


@dataclass(frozen=True)
class Var:
    name: str
    line: int
    col: int


@dataclass(frozen=True)
class Bin:
    op: str
    left: Any
    right: Any


@dataclass(frozen=True)
class Call:
    fn: str
    args: tuple


@dataclass(frozen=True)
class Assign:
    name: str
    expr: Any


@dataclass(frozen=True)
class If:
    cond: Any
    then: tuple
    other: tuple


@dataclass(frozen=True)
class Pay:
    expr: Any


@dataclass(frozen=True)
class Stop:
    pass


@dataclass(frozen=True)
class Program:
    states: tuple                 # ((name, expr), ...)
    events: tuple                 # ((schedule name, block), ...) in script order


class _Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0

    def peek(self, text=None):
        t = self.toks[self.i]
        return t if text is None or t.text == text else None

    def take(self, text=None, kind=None):
        t = self.toks[self.i]
        if (text is not None and t.text != text) or (kind is not None and t.kind != kind):
            want = repr(text) if text else kind
            raise ScriptError(f"expected {want}, found {t.text or 'end of script'!r}", t.line, t.col)
        self.i += 1
        return t

    def program(self) -> Program:
        states, events = [], []
        while self.peek().kind != "end":
            if self.peek("state"):
                self.take("state")
                name = self.take(kind="name").text
                self.take("=")
                states.append((name, self.expr()))
                self.take(";")
            else:
                self.take("at")
                events.append((self.take(kind="name").text, self.block()))
        return Program(tuple(states), tuple(events))

    def block(self) -> tuple:
        self.take("{")
        body = []
        while not self.peek("}"):
            body.append(self.stmt())
        self.take("}")
        return tuple(body)

    def stmt(self):
        t = self.peek()
        if t.text == "if":
            self.take("if")
            cond, then = self.expr(), self.block()
            other = ()
            if self.peek("else"):
                self.take("else")
                other = (self.stmt(),) if self.peek("if") else self.block()
            return If(cond, then, other)
        if t.text == "pay":
            self.take("pay")
            e = self.expr()
            self.take(";")
            return Pay(e)
        if t.text == "stop":
            self.take("stop")
            self.take(";")
            return Stop()
        name = self.take(kind="name").text
        self.take("=")
        e = self.expr()
        self.take(";")
        return Assign(name, e)

    def expr(self):
        left = self.and_()
        while self.peek("or"):
            self.take("or")
            left = Bin("or", left, self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.peek("and"):
            self.take("and")
            left = Bin("and", left, self.not_())
        return left

    def not_(self):
        if self.peek("not"):
            self.take("not")
            return Bin("not", Num(0.0), self.not_())
        return self.cmp()

    def cmp(self):
        left = self.sum()
        if self.peek().text in ("<", "<=", ">", ">=", "==", "!="):
            op = self.take().text
            left = Bin(op, left, self.sum())
        return left

    def sum(self):
        left = self.term()
        while self.peek().text in ("+", "-"):
            op = self.take().text
            left = Bin(op, left, self.term())
        return left

    def term(self):
        left = self.unary()
        while self.peek().text in ("*", "/"):
            op = self.take().text
            left = Bin(op, left, self.unary())
        return left

    def unary(self):
        if self.peek("-"):
            self.take("-")
            return Bin("-", Num(0.0), self.unary())
        return self.atom()

    def atom(self):
        t = self.peek()
        if t.kind == "num":
            self.take()
            return Num(float(t.text))
        if t.text == "(":
            self.take("(")
            e = self.expr()
            self.take(")")
            return e
        name = self.take(kind="name")
        if self.peek("("):
            if name.text not in FUNCS:
                raise ScriptError(f"unknown function {name.text!r}", name.line, name.col)
            self.take("(")
            args = [self.expr()]
            while self.peek(","):
                self.take(",")
                args.append(self.expr())
            self.take(")")
            return Call(name.text, tuple(args))
        return Var(name.text, name.line, name.col)


def parse(text: str) -> Program:
    return _Parser(tokenize(text)).program()


def schedule(program: Program, dates: dict) -> list[tuple]:
    """The event schedule: every (date, block index), in date order, script order within a date."""
    ev = []
    for k, (name, _block) in enumerate(program.events):
        if name not in dates:
            raise ScriptError(f"no schedule named {name!r}", 0, 0)
        ev += [(d, k) for d in dates[name]]
    return sorted(ev, key=lambda x: (x[0], x[1]))


# ------------------------------------------------------------ evaluation
_OPS = {"+": np.add, "-": np.subtract, "*": np.multiply, "/": np.divide, "<": np.less, "<=": np.less_equal,
        ">": np.greater, ">=": np.greater_equal, "==": np.equal, "!=": np.not_equal}


def _eval(e, env):
    """One expression; works on floats (interpreter) and on arrays (compiled) alike."""
    if isinstance(e, Num):
        return e.value
    if isinstance(e, Var):
        if e.name not in env:
            raise ScriptError(f"undefined name {e.name!r}", e.line, e.col)
        return env[e.name]
    if isinstance(e, Call):
        a = [_eval(x, env) for x in e.args]
        if e.fn == "abs":
            return np.abs(a[0])
        f = np.minimum if e.fn == "min" else np.maximum
        out = a[0]
        for x in a[1:]:
            out = f(out, x)
        return out
    if e.op == "and":
        return np.logical_and(_eval(e.left, env), _eval(e.right, env))
    if e.op == "or":
        return np.logical_or(_eval(e.left, env), _eval(e.right, env))
    if e.op == "not":
        return np.logical_not(_eval(e.right, env))
    return _OPS[e.op](_eval(e.left, env), _eval(e.right, env))


class Interpreter:
    """Walks the tree once per path and per event: simple, and slow."""

    def __init__(self, program: Program):
        self.p = program

    def run(self, perf, spot, events, times, dfs, params) -> np.ndarray:
        n = perf.shape[0]
        pv = np.zeros(n)
        for i in range(n):
            env = dict(params)
            for name, e in self.p.states:
                env[name] = float(_eval(e, env))
            alive = True
            for j, k in events:
                if not alive:
                    break
                env.update(S=float(spot[i, j]), perf=float(perf[i, j]), t=float(times[j]))
                paid, alive = self._block(self.p.events[k][1], env)
                pv[i] += paid * dfs[j]
        return pv

    def _block(self, stmts, env):
        paid = 0.0
        for s in stmts:
            if isinstance(s, Assign):
                env[s.name] = float(_eval(s.expr, env))
            elif isinstance(s, Pay):
                paid += float(_eval(s.expr, env))
            elif isinstance(s, Stop):
                return paid, False
            else:
                branch = s.then if bool(_eval(s.cond, env)) else s.other
                more, alive = self._block(branch, env)
                paid += more
                if not alive:
                    return paid, False
        return paid, True


def compile_program(program: Program):
    """The same semantics on all paths at once: each statement under a mask of its paths."""

    def block(stmts, env, mask, pay, alive):
        for s in stmts:
            live = mask & alive
            if isinstance(s, Assign):
                old = env[s.name] if s.name in env else 0.0
                env[s.name] = np.where(live, _eval(s.expr, env), old)
            elif isinstance(s, Pay):
                pay += np.where(live, _eval(s.expr, env), 0.0)
            elif isinstance(s, Stop):
                alive &= ~live
            else:
                c = np.asarray(_eval(s.cond, env), bool)
                block(s.then, env, live & c, pay, alive)
                block(s.other, env, live & ~c, pay, alive)

    def run(perf, spot, events, times, dfs, params) -> np.ndarray:
        n = perf.shape[0]
        env = {k: np.full(n, float(v)) for k, v in params.items()}
        for name, e in program.states:
            env[name] = np.broadcast_to(np.asarray(_eval(e, env), float), (n,)).copy()
        pv, alive = np.zeros(n), np.ones(n, bool)
        for j, k in events:
            env.update(S=spot[:, j], perf=perf[:, j], t=np.full(n, times[j]))
            pay = np.zeros(n)
            block(program.events[k][1], env, np.ones(n, bool), pay, alive)
            pv += pay * dfs[j]
        return pv

    return run


# ------------------------------------------------------------ a scripted instrument in the pricing library
@FP.instrument_type
@dataclasses.dataclass(frozen=True, kw_only=True)
class ScriptedInstrument(FP.Instrument):
    script: str
    dates: tuple                   # ((schedule name, (date, ...)), ...)
    params: tuple = ()             # ((name, value), ...)
    underlyings: tuple = ()
    initial: tuple = ()


@dataclasses.dataclass(frozen=True)
class ScriptEngine:
    n_paths: int = 100_000
    mode: str = "compiled"
    name: str = "Script"

    def supports(self, inst, model) -> bool:
        return isinstance(inst, ScriptedInstrument) and type(model) is FP.BlackScholes

    def cashflows(self, inst: ScriptedInstrument, model, md: FP.MarketData) -> np.ndarray:
        prog = parse(inst.script)
        ev = schedule(prog, dict(inst.dates))
        dates = sorted({d for d, _k in ev})
        idx = {d: j for j, d in enumerate(dates)}
        names = inst.underlyings or (inst.underlying,)
        refs = [md.spots[u] for u in names]
        mc = FP.MonteCarloEngine(n_paths=self.n_paths)
        s = mc.paths(inst, md, list(names), dates, refs, model)
        init = np.array(inst.initial or refs)
        perf = (s / init[None, None, :]).min(axis=2)
        times = np.array([md.t(d) for d in dates])
        dfs = np.array([md.df(inst.curve(md), d) for d in dates])
        events = [(idx[d], k) for d, k in ev]
        run = compile_program(prog) if self.mode == "compiled" else Interpreter(prog).run
        return inst.notional * run(perf, s[:, :, 0], events, times, dfs, dict(inst.params))

    def price(self, inst, model, md) -> float:
        return float(self.cashflows(inst, model, md).mean())


FP.register(ScriptedInstrument, FP.BlackScholes, ScriptEngine())


def dates_after(asof: dt.date, months: int, n: int) -> tuple:
    return tuple(asof + dt.timedelta(days=round(30.4375 * months * (i + 1))) for i in range(n))


# ------------------------------------------------------------ observers and lazy recalculation
class Observable:
    def __init__(self):
        self._observers: list = []

    def register(self, obs) -> None:
        self._observers.append(obs)

    def notify(self) -> None:
        for o in self._observers:
            o.update()


class Quote(Observable):
    """A market quote that tells its observers when it changes."""

    def __init__(self, value: float):
        super().__init__()
        self._value = value

    @property
    def value(self) -> float:
        return self._value

    def set(self, value: float) -> None:
        if value != self._value:
            self._value = value
            self.notify()


class LazyPrice(Observable):
    """A price marked stale when an input changes, recomputed only when it is asked for."""

    def __init__(self, compute, *inputs):
        super().__init__()
        self.compute, self.inputs = compute, inputs
        self.cached, self.stale, self.calculations = None, True, 0
        for q in inputs:
            q.register(self)

    def update(self) -> None:
        if not self.stale:
            self.stale = True
            self.notify()                   # observers of this price are stale too

    @property
    def value(self) -> float:
        if self.stale:
            self.cached = self.compute(*(q.value for q in self.inputs))
            self.calculations += 1
            self.stale = False
        return self.cached
