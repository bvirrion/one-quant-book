"""Python and pandas: each printed program is run and its output compared; each function meets a second route.

Printed programs are run in a subprocess with this interpreter. Versions are stated in the stems: CPython 3.10,
NumPy 2.2 and pandas 2.3. A test that depends on one of those skips with a reason on another version.
Question numbers appear here only as test_q<N> and NONNUMERIC keys.
"""
import csv
import dis
import math
import multiprocessing
import pathlib
import random
import statistics
import subprocess
import sys
import threading
import time
import tracemalloc
import warnings
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
PY = HERE / "python"
sys.path.insert(0, str(PY))
is_310 = sys.version_info[:2] == (3, 10)
needs_310 = pytest.mark.skipif(not is_310, reason="the printed behaviour is CPython 3.10's")
old_pandas = pd.__version__.startswith("2.")
needs_pandas2 = pytest.mark.skipif(not old_pandas, reason="the printed behaviour is pandas 2's")

import iv_asof_numpy  # noqa: E402
import iv_async  # noqa: E402
import iv_bars  # noqa: E402
import iv_clean_ticks  # noqa: E402
import iv_context  # noqa: E402
import iv_correlated  # noqa: E402
import iv_dataclass  # noqa: E402
import iv_ewma  # noqa: E402
import iv_exact_sum  # noqa: E402
import iv_group_ols  # noqa: E402
import iv_growth  # noqa: E402
import iv_ic  # noqa: E402
import iv_mc_call  # noqa: E402
import iv_memo  # noqa: E402
import iv_merge_asof  # noqa: E402
import iv_noise_backtest  # noqa: E402
import iv_position  # noqa: E402
import iv_rolling_beta  # noqa: E402
import iv_sort  # noqa: E402
import iv_stream_csv  # noqa: E402
import iv_vwap  # noqa: E402

NONNUMERIC = {}


def show(name):
    r = subprocess.run([sys.executable, str(PY / f"{name}.py")], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


def test_q1():
    assert show("pp_default") == ["[1]", "[1, 2]", "[3]", "[1, 2, 4]"]
    def add(x, items=None):
        if items is None:
            items = []
        items.append(x)
        return items
    assert add(1) == [1] and add(2) == [2]
    mine = []
    assert add(3, mine) is mine and mine == [3]


def test_q2():
    assert show("pp_alias") == ["{'A': [1], 'B': [1]}", "[[9, 0], [9, 0]]"]
    d = {k: [] for k in "AB"}
    d["A"].append(1)
    assert d == {"A": [1], "B": []}
    g = [[0] * 2 for _ in range(2)]
    g[0][0] = 9
    assert g == [[9, 0], [0, 0]]
    z = dict.fromkeys("AB", 0)
    z["A"] += 1
    assert z == {"A": 1, "B": 0}


@needs_310
def test_q3():
    assert show("pp_is") == ["True True", "False True"]
    assert (np.bool_(True) is True) is False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert eval("257 is 257") is True


def test_q4():
    out = show("pp_keys")
    assert out[0] == "tuple" and out[1].startswith("TypeError") and out[2].startswith("TypeError") and out[3] == "absent"
    if is_310:
        assert sys.getsizeof((1, 2)) == 56 and sys.getsizeof([1, 2]) == 72
    t = (1, [2])
    t[1].append(3)
    assert t == (1, [2, 3])


def test_q5():
    assert show("pp_copy") == ["{'A': [1, 2, 3]}", "{'A': [1, 2]}"]
    a = np.arange(3)
    b = a.copy()
    b[0] = 9
    assert a[0] == 0


@needs_310
def test_q6():
    assert show("pp_nan") == ["False True False", "nan 1.0", "[2.0, nan, 1.0]"]
    prices = [1.0, float("nan"), 3.0]
    assert max(x for x in prices if not math.isnan(x)) == 3.0 and np.nanmax(prices) == 3.0


def test_q7():
    assert show("pp_exhaust") == ["[(1, 3), (2, 4)]", "[]", "5 0", "3 3"]
    def mean_sum_first(xs):
        s = sum(xs)
        return s / sum(1 for _ in xs)
    def mean_count_first(xs):
        n = sum(1 for _ in xs)
        return sum(xs) / n
    gen = (float(x) for x in (1, 2, 3))
    with pytest.raises(ZeroDivisionError):
        mean_sum_first(gen)
    assert mean_count_first(float(x) for x in (1, 2, 3)) == 0.0  # silently wrong
    assert mean_count_first([1.0, 2.0, 3.0]) == 2.0
    it = iter([1])
    assert iter(it) is it


def test_q8():
    assert show("pp_overflow") == ["[-2147483648]", "[255]", "2147483648"]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        np.array([2**31 - 1], dtype=np.int32) + 1  # noqa: B018 - an array gives no warning
    with pytest.warns(RuntimeWarning):
        np.int32(2**31 - 1) + 1  # noqa: B018
    a = np.array([2**30, 2**30], dtype=np.int32)
    assert a.cumsum(dtype=np.int32)[-1] == -(2**31)
    # the check that cannot fail: the first difference wraps back to the input; the two that can
    b = np.array([2**30] * 3, dtype=np.int32)
    running = b.cumsum(dtype=np.int32)
    assert (np.diff(running) == b[1:]).all()
    assert int(running[-1]) != sum(int(v) for v in b) and (running[1:] < running[:-1]).any()


def test_q9():
    assert show("pp_series_and") == ["A ValueError", "B ValueError", "C [2]"]
    df = pd.DataFrame({"qty": [1, 2, 3], "px": [4.5, 5.5, 6.5]})
    with pytest.raises(TypeError):
        df[df.qty > 1 & df.px < 6]  # noqa: B015
    assert list(pd.DataFrame({"qty": [1, 2, 3], "px": [4, 5, 6]}).query("qty > 1 and px < 6").qty) == [2]
    with pytest.raises(ValueError, match="truth value of an array with more than one element"):
        np.array([True, False]) and np.array([True, True])  # noqa: B018
    assert bool(np.array([True]))  # one element is not refused


counter_for_q10 = 0


def test_q10():
    code = compile("count += 1", "<s>", "exec")
    names = [i.opname for i in dis.get_instructions(code)]
    assert "LOAD_NAME" in names and "STORE_NAME" in names and names.index("LOAD_NAME") < names.index("STORE_NAME")
    between = threading.Barrier(4)
    def racy(n):
        global counter_for_q10
        for _ in range(n):
            tmp = counter_for_q10
            between.wait()  # every thread has read before any writes: the interleaving is forced, not hoped for
            counter_for_q10 = tmp + 1
            between.wait()
    ts = [threading.Thread(target=racy, args=(300,)) for _ in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert counter_for_q10 == 300  # of 1200: in each round, four increments count as one
    lock, box = threading.Lock(), [0]
    def safe(n):
        for _ in range(n):
            with lock:
                tmp = box[0]
                time.sleep(0)
                box[0] = tmp + 1
    ts = [threading.Thread(target=safe, args=(300,)) for _ in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert box[0] == 1200
    from multiprocessing import shared_memory
    block = shared_memory.SharedMemory(create=True, size=800)
    try:
        arr = np.ndarray((100,), dtype=np.int64, buffer=block.buf)
        arr[:] = 7
        def child(name):
            other = shared_memory.SharedMemory(name=name)
            view = np.ndarray((100,), dtype=np.int64, buffer=other.buf)
            view[3] = 9
            del view
            other.close()
        worker = multiprocessing.get_context("fork").Process(target=child, args=(block.name,))
        worker.start()
        worker.join(60)
        assert worker.exitcode == 0
        assert arr[3] == 9 and arr[4] == 7  # the other process wrote to the same memory
        del arr
    finally:
        block.close()
        block.unlink()


def test_q11():
    calls = [0]
    @iv_memo.memo
    def fib(n):
        """Doc."""
        calls[0] += 1
        return n if n < 2 else fib(n - 1) + fib(n - 2)
    assert fib(30) == 832040 and calls[0] == 31
    assert fib.__name__ == "fib" and fib.__doc__ == "Doc."
    def plain_calls(n):  # c(n) = c(n - 1) + c(n - 2) + 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b + 1
        return b
    calls[0] = 0
    def slow(n):
        calls[0] += 1
        return n if n < 2 else slow(n - 1) + slow(n - 2)
    slow(20)
    assert calls[0] == plain_calls(20)
    a, b = 0, 1
    for _ in range(31):
        a, b = b, a + b
    assert plain_calls(30) == 2 * a - 1 == 2692537
    n = [0]
    @iv_memo.memo
    def f(a, b=0):
        n[0] += 1
        return a + b
    assert f(1, 2) == f(1, b=2) == 3 and n[0] == 2
    with pytest.raises(TypeError):
        f([1])
    # the wrong form recomputes a result that is falsy
    seen, cache = [0], {}
    def g(x):
        seen[0] += 1
        return 0
    for _ in range(3):
        cache[1] = cache.get(1) or g(1)
    assert seen[0] == 3


def test_q12(tmp_path):
    rng = random.Random(12)
    path = tmp_path / "t.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "price_ticks", "qty"])
        for _ in range(200_000):
            w.writerow([rng.choice("ABCDE"), rng.randint(1, 999), rng.randint(1, 99)])
    got = iv_stream_csv.notional_by_symbol(iv_stream_csv.rows(path))
    df = pd.read_csv(path)
    want = (df.price_ticks * df.qty).groupby(df.symbol).sum().to_dict()
    assert got == want
    tracemalloc.start()
    iv_stream_csv.notional_by_symbol(iv_stream_csv.rows(path))
    stream_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    tracemalloc.start()
    held = list(iv_stream_csv.rows(path))
    list_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert len(held) == 200_000 and stream_peak < 1_000_000 < 10_000_000 < list_peak
    # the file closes when the generator is closed
    gen = iv_stream_csv.rows(path)
    next(gen)
    frame_file = gen.gi_frame.f_locals["f"]
    assert not frame_file.closed
    gen.close()
    assert frame_file.closed
    gen = iv_stream_csv.rows(path)
    next(gen)
    frame_file = gen.gi_frame.f_locals["f"]
    del gen  # reference counting runs the finally of the with
    assert frame_file.closed


def test_q13():
    assert show("pp_class_attr") == ["[1]", "[9] [1]"]
    class Prop:
        @property
        def x(self):
            return "class"
    p = Prop()
    p.__dict__["x"] = "instance"
    assert p.x == "class"  # a data descriptor beats the instance
    with pytest.raises(AttributeError):
        p.x = 1  # and assignment goes through it
    class Plain:
        def __init__(self):
            self.a, self.b = 1, 2
    class Slotted:
        __slots__ = ("a", "b")
        def __init__(self):
            self.a, self.b = 1, 2
    def per_object(cls):
        tracemalloc.start()
        keep = [cls() for _ in range(20_000)]
        used = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        assert len(keep) == 20_000
        return used / 20_000
    if is_310:
        assert per_object(Slotted) * 2 < per_object(Plain)
    s = Slotted()
    assert not hasattr(s, "__dict__")
    with pytest.raises(AttributeError):
        s.qyt = 1
    with pytest.raises(ValueError):
        class Bad:
            __slots__ = ("orders",)
            orders = []


def test_q14():
    for make in (iv_context.Held, iv_context.held):
        log = []
        with pytest.raises(KeyError):
            with make(log):
                raise KeyError("x")
        assert log == ["acquire", "release"]
        log = []
        with make(log):
            pass
        assert log == ["acquire", "release"]
    class Swallow(iv_context.Held):
        def __exit__(self, *a):
            super().__exit__(*a)
            return True
    log = []
    with Swallow(log):
        raise KeyError("gone")
    assert log == ["acquire", "release"]
    from contextlib import contextmanager
    @contextmanager
    def careless(log):
        log.append("acquire")
        yield
        log.append("release")
    log = []
    with pytest.raises(KeyError):
        with careless(log):
            raise KeyError("x")
    assert log == ["acquire"]  # never released
    class Raises(iv_context.Held):
        def __exit__(self, *a):
            raise ValueError("release failed")
    with pytest.raises(ValueError) as e:
        with Raises([]):
            raise KeyError("first")
    assert isinstance(e.value.__context__, KeyError)


def test_q15():
    from dataclasses import FrozenInstanceError, dataclass, field
    with pytest.raises(ValueError):
        @dataclass
        class Bad:
            tags: list = []  # noqa: RUF008
    a, b = iv_dataclass.Order(1, 2), iv_dataclass.Order(3, 4)
    a.tags.append("x")
    assert b.tags == []
    with pytest.raises(TypeError):
        {a}  # noqa: B018
    k = iv_dataclass.Key("A", "X")
    assert len({k, iv_dataclass.Key("A", "X")}) == 1
    with pytest.raises(FrozenInstanceError):
        k.symbol = "B"
    @dataclass(frozen=True)
    class F:
        tags: list = field(default_factory=list)
    f = F()
    f.tags.append(1)
    assert f.tags == [1]
    with pytest.raises(TypeError):
        hash(f)
    @dataclass(slots=True)
    class S:
        x: int
    assert not hasattr(S(1), "__dict__")
    @dataclass(unsafe_hash=True)
    class U:
        x: int
    u = U(1)
    s = {u}
    u.x = 2
    assert u not in s  # lost


def test_q16():
    f = iv_sort.by_symbol_then_notional
    t = [("B", 5), ("A", 1), ("A", 3), ("B", 5), ("A", 3)]
    tagged = [(s, n, i) for i, (s, n) in enumerate(t)]
    got = f(tagged)
    assert [(a, b) for a, b, _ in got] == [("A", 3), ("A", 3), ("A", 1), ("B", 5), ("B", 5)]
    assert [g[2] for g in got if g[1] == 3] == [2, 4]  # ties keep their order, reverse=True included
    assert [g[2] for g in got if g[1] == 5] == [0, 3]
    assert [g[2] for g in sorted(tagged, key=lambda x: x[1])[::-1] if g[1] == 5] == [3, 0]  # slicing flips ties
    assert sorted(t, key=lambda x: (x[0], -x[1])) == [(a, b) for a, b, _ in got]
    rng = random.Random(16)
    for _ in range(300):
        xs = [(rng.choice("ABC"), rng.randint(0, 3), i) for i in range(rng.randint(0, 10))]
        assert f(xs) == sorted(xs, key=lambda x: (x[0], -x[1], x[2]))
    with pytest.raises(TypeError):
        sorted([None, 1])  # the two-pass form still needs a key that orders
    with pytest.raises(TypeError, match="unary -"):
        sorted([("A", None)], key=lambda x: (x[0], -x[1]))  # the one-pass key fails earlier, at the negation
    assert [v for v in sorted([3, None, 1], key=lambda v: (v is None, v or 0))] == [1, 3, None]


def test_q17():
    r = np.array([[1.0, 2.0], [3.0, 6.0]])
    wrong, right = r - r.mean(axis=1), r - r.mean(axis=1, keepdims=True)
    assert wrong.tolist() == [[-0.5, -2.5], [1.5, 1.5]] and right.tolist() == [[-0.5, 0.5], [-1.5, 1.5]]
    assert wrong.sum(axis=1).tolist() == [-3.0, 3.0] and right.sum(axis=1).tolist() == [0.0, 0.0]
    one_stock = np.ones((3, 1))
    assert (one_stock - one_stock.mean(axis=1)).shape == (3, 3)  # non-square, and still silent
    with pytest.raises(ValueError):
        np.zeros((2, 3)) - np.zeros((2, 3)).mean(axis=1)
    out = subprocess.run([sys.executable, str(PY / "pp_broadcast.py")], capture_output=True, text=True).stdout
    assert "-2.5" in out and "1.5" in out


@needs_pandas2
def test_q18():
    assert show("pp_views") == ["[ 0 99  2  3  4]"]
    a = np.arange(5)
    assert np.shares_memory(a, a[1:3]) and not np.shares_memory(a, a[[3, 4]]) and not np.shares_memory(a, a[a > 3])
    assert a[:2].base is a and a[:2].copy().base is None
    df = pd.DataFrame({"x": [1, -1], "y": [0, 0]})
    with pytest.warns(pd.errors.SettingWithCopyWarning):
        df[df.x > 0]["y"] = 1
    assert df.y.tolist() == [0, 0]
    df.loc[df.x > 0, "y"] = 1
    assert df.y.tolist() == [1, 0]
    b = np.arange(3)
    b.flags.writeable = False
    with pytest.raises(ValueError):
        b[0] = 1


def test_q19():
    df = pd.DataFrame([("A", 1, 10, 100), ("A", 1, 11, 300), ("B", 1, 20, 50), ("A", 2, 12, 0)],
                      columns=["symbol", "day", "price", "qty"])
    v = iv_vwap.vwap_by_symbol_day(df)
    assert v.loc[("A", 1)] == 10.75 and v.loc[("B", 1)] == 20 and math.isnan(v.loc[("A", 2)])
    assert df[(df.symbol == "A") & (df.day == 1)].price.mean() == 10.5
    rng = np.random.default_rng(19)
    big = pd.DataFrame({"symbol": rng.choice(list("ABC"), 500), "day": rng.integers(1, 5, 500),
                        "price": rng.integers(1, 50, 500), "qty": rng.integers(1, 50, 500)})
    slow = {}
    for (s, d), g in big.groupby(["symbol", "day"]):
        slow[(s, d)] = Fraction(int((g.price * g.qty).sum()), int(g.qty.sum()))
    fast = iv_vwap.vwap_by_symbol_day(big)
    assert all(math.isclose(fast.loc[k], float(x)) for k, x in slow.items()) and len(fast) == len(slow)
    # all prices equal: the average is that price whatever the sizes
    flat = big.assign(price=7)
    assert (iv_vwap.vwap_by_symbol_day(flat) == 7).all()


def test_q20():
    tr = pd.DataFrame({"t": [1, 5, 10], "symbol": "X"})
    qu = pd.DataFrame({"t": [2, 5, 9], "symbol": "X", "q": [2, 5, 9]})
    def go(**kw):
        return pd.merge_asof(tr, qu, on="t", by="symbol", **kw).q.tolist()
    assert iv_merge_asof.quotes_at_trades(tr, qu).q.fillna(-1).tolist() == [-1, 5, 9]
    assert np.isnan(go()[0]) and go()[1:] == [5, 9]
    x = go(allow_exact_matches=False)
    assert np.isnan(x[0]) and x[1:] == [2, 9]
    y = go(direction="forward")
    assert y[:2] == [2, 5] and np.isnan(y[2])
    with pytest.raises(ValueError, match="sorted"):
        pd.merge_asof(tr.iloc[::-1], qu, on="t", by="symbol")
    two = pd.merge_asof(pd.DataFrame({"t": [5], "symbol": ["Y"]}), qu, on="t", by="symbol")
    assert np.isnan(two.q[0])  # stays inside its symbol
    z = pd.merge_asof(tr, qu, on="t", by="symbol", tolerance=1).q.tolist()
    assert np.isnan(z[0]) and z[1:] == [5, 9]
    rng = random.Random(20)
    for _ in range(100):
        ts = sorted(rng.sample(range(40), 6))
        qs = sorted(rng.sample(range(40), 6))
        got = pd.merge_asof(pd.DataFrame({"t": ts}), pd.DataFrame({"t": qs, "q": qs}), on="t").q.tolist()
        for t, g in zip(ts, got, strict=True):
            prior = [q for q in qs if q <= t]
            assert (np.isnan(g) and not prior) or g == prior[-1]


def test_q21():
    idx = pd.to_datetime(["2026-01-05 09:30:10", "2026-01-05 09:30:50", "2026-01-05 09:31:20", "2026-01-05 09:33:05"])
    p = pd.Series([10.0, 12.0, 11.0, 13.0], index=idx)
    default = p.resample("1min").ohlc()
    first = default.iloc[0]
    assert default.index[0].strftime("%H:%M") == "09:30"
    assert (first.open, first.high, first.low, first.close) == (10, 12, 10, 12)
    assert default.loc["2026-01-05 09:32"].isna().all()
    b = iv_bars.minute_bars(p)
    assert b.index[0].strftime("%H:%M") == "09:31" and b.iloc[0].close == 12
    row = b.loc["2026-01-05 09:33"]  # the empty minute 09:32, labelled at its end
    assert row.close == 11 and np.isnan(row.open)


def test_q22():
    assert show("pp_align") == ["[nan, 12.0, 23.0, nan]", "[11, 22, 33]", "[1.0, 12.0, 23.0, 30.0]"]
    rng = np.random.default_rng(22)
    days = np.arange(2_000)
    common = rng.normal(0, 0.01, 2_000)
    one = pd.Series(100 * np.exp(np.cumsum(common)), index=days)
    two = pd.Series(50 * np.exp(np.cumsum(common + rng.normal(0, 0.002, 2_000))), index=days).drop(500)
    two.loc[2_000] = two.iloc[-1]  # a later day makes up the count
    pair = one.reindex(two.index[:-1])
    lined_up = np.corrcoef(one.diff().dropna(), two.reindex(one.index).ffill().diff().dropna())[0, 1]
    by_position = np.corrcoef(np.diff(one.values), np.diff(two.values))[0, 1]
    assert len(one) == len(two) and len(pair) == 1_999 and lined_up > 0.9 and by_position < 0.5
    f = pd.Series([1.0, 2.0, 3.0], index=[1, 2, 3])
    assert list(f.index.difference(pd.Index([2, 3, 4]))) == [1]


def test_q23():
    with_look, with_shift = iv_noise_backtest.sharpes()
    daily = math.sqrt(2 / math.pi) / math.sqrt(1 - 2 / math.pi)
    assert round(daily, 4) == 1.3236 and round(daily * math.sqrt(252), 1) == 21.0
    assert abs(with_look - daily * math.sqrt(252)) < 0.3 and abs(with_shift) < 0.3
    assert round(with_look, 1) == 21.1 and round(with_shift, 2) == -0.03
    # the same for any sigma: Sharpe has no units
    rng = np.random.default_rng(1)
    r = rng.normal(0, 5.0, 200_000)
    assert abs(np.abs(r).mean() / np.abs(r).std() - daily) < 0.01


def test_q24():
    assert show("pp_nan_pandas") == ["4.0 2.0 2 3 1.33", "0.0 nan", "{'A': 4}", "False"]
    df = pd.DataFrame({"k": ["A", None, "A"], "v": [1, 2, 3]})
    assert df.groupby("k", dropna=False).v.sum().sum() == 6
    p = pd.Series([100.0, np.nan, 102.0])
    r = p.fillna(0).pct_change()
    assert r.iloc[1] == -1 and np.isinf(r.iloc[2])
    assert math.isclose(p.ffill().pct_change().iloc[2], 0.02)


def test_q25(tmp_path):
    syms = [f"S{i % 4000:04d}" for i in range(200_000)]
    syms = ["".join(list(s)) for s in syms]  # one string object per row, as from the csv module
    plain = pd.Series(syms, dtype=object)
    cat = plain.astype("category")
    assert cat.cat.codes.dtype == np.int16 and cat.memory_usage(deep=True) * 10 < plain.memory_usage(deep=True)
    if is_310:
        assert sys.getsizeof("S0001") == 54 and 8 + 53 == 61 and round(61 * 100e6 / 1e9, 1) == 6.1
    assert 100_000_000 * 8 == 800_000_000 and 100_000_000 * 2 == 200_000_000
    # a real file: the csv module makes a string per row, and read_csv's C parser shares them
    path = tmp_path / "t.csv"
    rows = 400_000
    path.write_text("symbol,price,qty\n" + "".join(f"S{i % 4000:04d},101.25,5\n" for i in range(rows)))
    with open(path, newline="") as f:
        by_csv = [r[0] for r in csv.reader(f)][1:]
    assert len({id(s) for s in by_csv}) == rows
    frame = pd.read_csv(path)
    objects = {id(s) for s in frame.symbol}
    assert len(objects) < rows / 10  # a set per internal chunk, not a string per row
    if is_310:
        deep = frame.symbol.memory_usage(deep=True) / rows  # still counts each element, so about 6 GB for the 100 million
        assert 60 < deep < 64
        real = (8 * rows + len(objects) * sys.getsizeof("S0001")) / rows
        assert real < 12  # about 1 GB for the 100 million, and about four times the 2 bytes of a code
        assert 8 / 2 == 4
    v = np.float32(2**24)
    assert v + np.float32(1) == v and 2**24 == 16_777_216
    p = float(np.float32(101.27))
    assert str(p).startswith("101.26999664") and p != 101.27
    assert math.isclose(float(np.spacing(np.float32(10_000))), 0.001, rel_tol=0.1)
    few = pd.Series([str(i) for i in range(1000)], dtype=object)
    assert few.astype("category").memory_usage(deep=True) > few.memory_usage(deep=True)  # worse with no repeats


def test_q26():
    assert 0.1 + 0.2 != 0.3 and repr(0.1 + 0.2) == "0.30000000000000004"
    assert 1e-13 == pytest.approx(0)
    assert 1e-9 != pytest.approx(0)
    assert 1e-9 == pytest.approx(0, abs=1e-8)
    assert 100.00001 == pytest.approx(100) and 100.001 != pytest.approx(100)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "vwap_checks.py"],
                       cwd=PY, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and "4 passed" in r.stdout, r.stdout
    assert math.ulp(1e12) > 1e-9  # a tolerance of 1e-9 is below the step at 1e12


@needs_310
def test_q27():
    assert np.round(2.5) == 2.0 and np.round(3.5) == 4.0 and float(np.round(2.675, 2)) == 2.68 != round(2.675, 2) == 2.67
    out = show("pp_round")
    assert out == ["2 4 2.67", "2.67499999999999982236431605997495353221893310546875", "False", "2.68"]
    assert np.round(2.5) == 2 and np.round(3.5) == 4
    assert Decimal("2.675").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("2.68")
    assert round(2.675 + 0.005, 2) == 2.68 and round(1.001 + 0.005, 2) == 1.01  # right once, and wrong on 1.001


@needs_310
def test_q28():
    xs = [1e16, 1.0, -1e16]
    assert sum(xs) == 0.0 and math.fsum(xs) == 1.0 and iv_exact_sum.neumaier(xs) == 1.0 and iv_exact_sum.kahan(xs) == 0.0
    assert math.ulp(1e16) == 2.0 and 1e16 + 1.0 == 1e16
    rng = random.Random(281)
    for _ in range(2000):  # for two doubles the dropped bits are exact
        a, b = sorted((rng.uniform(-1, 1) * 10.0 ** rng.randint(-8, 16) for _ in "ab"), key=abs, reverse=True)
        t = a + b
        assert Fraction(t) + Fraction((a - t) + b) == Fraction(a) + Fraction(b)
    tenth = [0.1] * 1_000_000
    assert round(abs(sum(tenth) - 100_000.0) * 1e6, 1) == 1.3
    assert math.fsum(tenth) == 100_000.0 and iv_exact_sum.neumaier(tenth) == 100_000.0
    assert sum(sorted(xs, key=abs)) == 0.0
    rng = random.Random(28)
    for _ in range(300):
        ys = [rng.uniform(-1, 1) * 10.0 ** rng.randint(-8, 14) for _ in range(rng.randint(1, 40))]
        exact = float(sum(Fraction(y) for y in ys))
        assert abs(iv_exact_sum.neumaier(ys) - exact) <= abs(sum(ys) - exact) + 4 * math.ulp(max(map(abs, ys), default=1.0))
        assert math.fsum(ys) == exact


def test_q29():
    import asyncio
    log = asyncio.run(iv_async.main(iv_async.handler_blocks))
    assert log == ["beat", "work", "work", "work", "beat", "beat"]
    log = asyncio.run(iv_async.main(iv_async.handler_yields))
    assert log.count("beat") == 3 and log.count("work") == 3
    assert log.index("beat", 1) < len(log) - 1 - log[::-1].index("work")  # a beat falls before the last work
    async def coro():
        return 1
    c = coro()
    assert asyncio.iscoroutine(c)
    with pytest.warns(RuntimeWarning, match="never awaited"):
        del c
        import gc
        gc.collect()


def test_q30():
    two = pd.DataFrame({"symbol": list("AAAAB"), "x": [1, 2, 3, 100.0, 1], "y": [2, 4, 6, np.nan, 1]})
    got = iv_group_ols.group_betas(two)
    assert got["A"] == 2 and np.isnan(got["B"])
    a = two[two.symbol == "A"]
    dx, dy = a.x - a.x.mean(), a.y - a.y.mean()
    assert a.x.mean() == 26.5 and round((dx * dy).sum() / (dx * dx).sum(), 5) == 0.00056
    flat = pd.DataFrame({"symbol": list("CCC"), "x": [1.0, 1.0, 1.0], "y": [1.0, 2.0, 3.0]})
    assert np.isnan(iv_group_ols.group_betas(flat)["C"])
    # a constant float x: the group mean can be off by one bit, and the slope must still be NaN, not rounding noise
    rng = np.random.default_rng(300)
    for _ in range(500):
        k = int(rng.integers(3, 30))
        g = pd.DataFrame({"symbol": ["C"] * k, "x": [float(rng.random())] * k, "y": rng.normal(size=k)})
        assert np.isnan(iv_group_ols.group_betas(g)["C"])
    tiny = pd.DataFrame({"symbol": list("DDD"), "x": [1.0, 1.0 + 1e-9, 1.0 + 2e-9], "y": [1.0, 3.0, 5.0]})
    assert math.isclose(iv_group_ols.group_betas(tiny)["D"], 2e9, rel_tol=1e-3)  # a small real spread is not masked
    rng = np.random.default_rng(30)
    n = 6000
    big = pd.DataFrame({"symbol": rng.integers(0, 40, n), "x": rng.normal(size=n)})
    big["y"] = big.symbol * 0.1 * big.x + rng.normal(size=n)
    big.loc[rng.random(n) < 0.1, "x"] = np.nan
    big.loc[rng.random(n) < 0.1, "y"] = np.nan
    fast = iv_group_ols.group_betas(big)
    for s, g in big.groupby("symbol"):
        g = g.dropna()
        assert math.isclose(fast[s], np.polyfit(g.x, g.y, 1)[0], rel_tol=1e-9)


def slow_clean(q, window=20, limit=0.05):
    rows = [r for r in q.itertuples(index=False) if r.bid > 0 and r.ask > r.bid]
    by = {}
    for r in sorted(rows, key=lambda r: (r.symbol, r.t)):  # sorted is stable
        by.setdefault(r.symbol, {})[r.t] = r               # last to arrive wins
    out = []
    for s, ticks in by.items():
        mids = []
        for t, r in ticks.items():
            mid = (r.bid + r.ask) / 2
            last = mids[-window:]
            if len(last) >= 5 and abs(mid / statistics.median(last) - 1) > limit:
                mids.append(mid)
                continue
            mids.append(mid)
            out.append((s, t, mid))
    return out


def test_q31():
    rng = random.Random(31)
    start = pd.Timestamp("2026-01-05 09:30")
    rows = []
    for s in ("A", "B"):
        mid = 100.0
        for _ in range(600):
            mid *= 1 + rng.gauss(0, 0.0005)
            t = start + pd.Timedelta(seconds=7 * rng.randint(0, 200)) + pd.Timedelta(days=rng.randint(0, 1))
            bid, ask = mid - 0.01, mid + 0.01
            u = rng.random()
            if u < 0.03:
                bid = 0.0
            elif u < 0.06:
                bid, ask = ask, bid
            elif u < 0.08:
                bid, ask = 1000.0, 1000.02
            rows.append((t, s, bid, ask))
    q = pd.DataFrame(rows, columns=["t", "symbol", "bid", "ask"])
    got = iv_clean_ticks.clean(q)
    want = slow_clean(q)
    assert sorted(zip(got.symbol, got.t, got.mid.round(8), strict=True)) == sorted((s, t, round(m, 8)) for s, t, m in want)
    assert (got.mid < 500).all() and len(got) < len(q)
    r = iv_clean_ticks.minute_returns(got)
    assert not r.dropna().empty and r.abs().max() < 0.05
    # slow route for the returns, one symbol and day at a time
    for (s, d), g in got.assign(day=got.t.dt.normalize()).groupby(["symbol", "day"]):
        last = {}
        for t, m in sorted(zip(g.t, g.mid, strict=True)):
            last[t.floor("min") + pd.Timedelta(minutes=1)] = m
        stamps = pd.date_range(min(last), max(last), freq="1min")
        filled, prev, age = [], np.nan, 0
        for st in stamps:
            if st in last:
                prev, age = last[st], 0
            else:
                age += 1
                if age > 5:
                    prev = np.nan
            filled.append(prev)
        want_r = np.diff(np.log(filled))
        got_r = r.loc[(s, d)].to_numpy()[1:]
        assert np.allclose(got_r, want_r, equal_nan=True)
        assert np.isnan(r.loc[(s, d)].to_numpy()[0])  # the first bar of a day has no return: no overnight
    # a true jump of 6%: ten ticks are lost, then all pass
    n = 60
    jump = pd.DataFrame({"t": pd.date_range(start, periods=n, freq="s"), "symbol": "J",
                         "bid": [99.99] * 30 + [105.99] * (n - 30), "ask": [100.01] * 30 + [106.01] * (n - 30)})
    kept = iv_clean_ticks.clean(jump)
    assert len(jump) - len(kept) == 10 and kept.t.iloc[30] == jump.t.iloc[40]
    # the warm-up: no past median for the first five ticks of a symbol, so a bad print there survives
    def bad_at(i):
        mids = [100.0] * 30
        mids[i] = 1000.0
        return pd.DataFrame({"t": pd.date_range(start, periods=30, freq="s"), "symbol": "W",
                             "bid": [m - 0.01 for m in mids], "ask": [m + 0.01 for m in mids]})
    assert (iv_clean_ticks.clean(bad_at(3)).mid > 500).any() and (iv_clean_ticks.clean(bad_at(4)).mid > 500).any()
    assert not (iv_clean_ticks.clean(bad_at(5)).mid > 500).any()


def test_q32():
    assert round(iv_ewma.Ewma(0.1).update(1.0), 4) == 1.0
    e = iv_ewma.Ewma(0.1)
    assert round([e.update(x) for x in (1.0, 2.0, 3.0)][-1], 4) == 2.0701 and round(5.61 / 2.71, 4) == 2.0701
    s = pd.Series([1.0, 2.0, 3.0])
    assert s.ewm(alpha=0.1, adjust=False).mean().round(10).tolist()[-1] == 1.29
    rng = np.random.default_rng(32)
    x = rng.normal(size=800)
    x[rng.random(800) < 0.1] = np.nan
    for alpha in (0.02, 0.1, 0.5, 1.0):
        e = iv_ewma.Ewma(alpha)
        mine = [e.update(float(v)) for v in x]
        assert np.allclose(mine, pd.Series(x).ewm(alpha=alpha).mean(), equal_nan=True)
    y = pd.Series(rng.normal(size=200))
    assert abs(y.ewm(alpha=0.1, adjust=True).mean().iloc[-1] - y.ewm(alpha=0.1, adjust=False).mean().iloc[-1]) < 1e-6
    secs = np.cumsum(rng.integers(0, 50, 300)).astype(float)
    z = rng.normal(size=300)
    e = iv_ewma.TimeEwma(7.0)
    mine = [e.update(t, float(v)) for t, v in zip(secs, z, strict=True)]
    stamps = pd.to_datetime(secs, unit="s")
    theirs = pd.Series(z, index=stamps).ewm(halflife=pd.Timedelta(seconds=7), times=stamps).mean()
    assert np.allclose(mine, theirs)
    z[rng.random(300) < 0.1] = np.nan  # NaN included, and a leading one
    z[0] = np.nan
    e = iv_ewma.TimeEwma(7.0)
    mine = [e.update(t, float(v)) for t, v in zip(secs, z, strict=True)]
    theirs = pd.Series(z, index=stamps).ewm(halflife=pd.Timedelta(seconds=7), times=stamps).mean()
    assert np.isnan(mine[0]) and not np.isnan(mine[-1]) and np.allclose(mine, theirs, equal_nan=True)
    e = iv_ewma.TimeEwma(2.0)
    e.update(0.0, 1.0)
    assert e.update(0.0, 3.0) == 2.0            # a shared stamp: equal weight
    assert abs(e.update(86_400.0, 9.0) - 9.0) < 1e-9  # a day later: the past is gone
    # a fixed alpha on uneven ticks depends on the message rate
    fixed = iv_ewma.Ewma(0.5)
    fixed.update(1.0)
    for _ in range(100):
        last = fixed.update(0.0)
    assert last < 1e-9


def test_q33():
    c = np.array([[1, 0.8], [0.8, 1]])
    lo = np.linalg.cholesky(c)
    assert np.allclose(lo, [[1, 0], [0.8, 0.6]]) and np.allclose(lo.T @ lo, [[1.64, 0.48], [0.48, 0.36]])
    assert round(0.48 / math.sqrt(1.64 * 0.36), 3) == 0.625
    rng = np.random.default_rng(33)
    z = rng.standard_normal((400_000, 2))
    assert np.allclose(np.cov((z @ lo).T), [[1.64, 0.48], [0.48, 0.36]], atol=0.02)
    three = np.array([[1, 0.8, 0.3], [0.8, 1, 0.5], [0.3, 0.5, 1.0]])
    assert np.allclose(np.corrcoef(iv_correlated.correlated_normals(three, 400_000, rng).T), three, atol=0.01)
    bad = np.array([[1, 0.9, 0.9], [0.9, 1, -0.9], [0.9, -0.9, 1.0]])
    assert np.allclose(np.linalg.eigvalsh(bad), [-0.8, 1.9, 1.9])
    with pytest.raises(np.linalg.LinAlgError):
        np.linalg.cholesky(bad)
    fixed = iv_correlated.nearest_correlation(bad)
    assert np.allclose(np.diag(fixed), 1) and np.allclose(fixed, [[1, 0.5, 0.5], [0.5, 1, -0.5], [0.5, -0.5, 1]], atol=1e-3)
    assert np.linalg.eigvalsh(fixed).min() > -1e-9
    np.linalg.cholesky(iv_correlated.nearest_correlation(np.array([[1, 0.5, 0.5], [0.5, 1, 0.5], [0.5, 0.5, 1.0]])))
    with pytest.raises(np.linalg.LinAlgError):
        np.linalg.cholesky(np.array([[1.0, 1.0], [1.0, 1.0]]))
    # a tiny addition to the diagonal does not rescue the bad matrix
    with pytest.raises(np.linalg.LinAlgError):
        np.linalg.cholesky(bad + 0.1 * np.eye(3))


def test_q34():
    from scipy.stats import norm
    def bs(s, k, r, v, t):
        d1 = (math.log(s / k) + (r + 0.5 * v * v) * t) / (v * math.sqrt(t))
        return s * norm.cdf(d1) - k * math.exp(-r * t) * norm.cdf(d1 - v * math.sqrt(t))
    assert round(bs(100, 100, 0.05, 0.2, 1), 4) == 10.4506
    p, e = iv_mc_call.mc_call(100, 100, 0.05, 0.2, 1, 1_000_000, np.random.default_rng(5))
    assert round(p, 4) == 10.4585 and round(e, 4) == 0.0073 and round((p - bs(100, 100, 0.05, 0.2, 1)) / e, 1) == 1.1
    z = np.random.default_rng(5).standard_normal(1_000_000)
    call = lambda w: np.maximum(100 * np.exp(0.03 + 0.2 * w) - 100, 0)  # noqa: E731
    both = math.exp(-0.05) * np.concatenate([call(z), call(-z)])
    assert round(both.std() / math.sqrt(2_000_000), 4) == 0.0104  # the naive error is too large for a call
    gaps = [(iv_mc_call.mc_call(100, k, 0.03, 0.3, 2, 20_000, np.random.default_rng(i)), k) for i, k in enumerate((80, 100, 130) * 10)]
    scores = [(p - bs(100, k, 0.03, 0.3, 2)) / e for (p, e), k in gaps]
    assert max(map(abs, scores)) < 4 and 0.5 < np.std(scores) < 1.5
    _, e1 = iv_mc_call.mc_call(100, 100, 0.05, 0.2, 1, 10_000, np.random.default_rng(1))
    _, e2 = iv_mc_call.mc_call(100, 100, 0.05, 0.2, 1, 1_000_000, np.random.default_rng(1))
    assert math.isclose(e1 / e2, 10, rel_tol=0.1)
    # chunking changes nothing but memory
    a = iv_mc_call.mc_call(100, 100, 0.05, 0.2, 1, 3000, np.random.default_rng(9), chunk=3000)
    b = iv_mc_call.mc_call(100, 100, 0.05, 0.2, 1, 3000, np.random.default_rng(9), chunk=1000)
    assert abs(a[0] - b[0]) < 1.0 and a[1] > 0 and b[1] > 0
    # exact checks: no volatility, and a strike of zero
    p, e = iv_mc_call.mc_call(100, 90, 0.05, 0.0, 1, 1000, np.random.default_rng(2))
    assert math.isclose(p, 100 - 90 * math.exp(-0.05)) and e < 1e-6
    p, e = iv_mc_call.mc_call(100, 0, 0.05, 0.2, 1, 200_000, np.random.default_rng(3))
    assert abs(p - 100) < 4 * e
    # a straddle at the forward: the members are positively correlated, so the naive error is too small
    w = np.random.default_rng(6).standard_normal(1_000_000)
    k = 100 * math.exp(0.03 + 0.02)
    strad = lambda v: np.abs(100 * np.exp(0.03 + 0.2 * v) - k)  # noqa: E731
    up, down = strad(w), strad(-w)
    assert np.corrcoef(up, down)[0, 1] > 0
    assert 0.5 * (up + down).std() / math.sqrt(1_000_000) > np.concatenate([up, down]).std() / math.sqrt(2_000_000)
    assert round(100 * 252 * 8 * 1_000_000 / 100 / 1e9, 1) == 2.0


def test_q35():
    assert iv_position.capped_position([9, -1], 8) == [8, 7]
    assert iv_position.wrong_clip([9, -1], 8) == [8, 8]
    assert iv_position.capped_above([9, -1], 8) == [8, 7]
    for q in range(-20, 21):  # one order alone can never show it
        assert iv_position.wrong_clip([q], 8) == iv_position.capped_position([q], 8)
    rng = random.Random(35)
    wrong_seen = 0
    for _ in range(500):
        xs = [rng.randint(-6, 6) for _ in range(rng.randint(1, 30))]
        cap = rng.randint(1, 10)
        pos, one_sided = 0, []
        for q in xs:
            pos = min(cap, pos + q)
            one_sided.append(pos)
        assert iv_position.capped_above(xs, cap) == one_sided
        assert all(abs(p) <= cap for p in iv_position.capped_position(xs, cap))
        wrong_seen += iv_position.wrong_clip(xs, cap) != iv_position.capped_position(xs, cap)
    assert wrong_seen > 200
    # a cap above every sum changes nothing, and clipping each order does not cap the position
    assert iv_position.capped_above([1, 2], 100) == [1, 3]
    assert np.cumsum(np.clip([5, 5, 5], -8, 8)).max() == 15


def test_q36():
    import gc
    import weakref
    from functools import lru_cache
    P = iv_growth.Pricer
    P.price.cache_clear()
    for _ in range(50):
        iv_growth.one_request(10)
    info = P.price.cache_info()
    assert (info.hits, info.misses, info.currsize) == (0, 50, 50)
    p = P(10)
    p.price(100)
    w = weakref.ref(p)
    del p
    gc.collect()
    assert w() is not None  # still held by the cache
    P.price.cache_clear()
    gc.collect()
    assert w() is None
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    for _ in range(50):
        iv_growth.one_request()
    top = tracemalloc.take_snapshot().compare_to(before, "lineno")[0]
    tracemalloc.stop()
    assert top.traceback[0].filename.endswith("iv_growth.py") and 3_950_000 < top.size_diff < 4_050_000  # 4.0 MB
    P.price.cache_clear()
    # both fixes let the instance go
    @lru_cache(maxsize=128)
    def price(strike, rate):
        return strike * rate
    class Own:
        def __init__(self):
            self.cache = {}
        def price(self, strike):
            return self.cache.setdefault(strike, strike * 0.01)
    class ByValue:
        rate = 0.01
        def price(self, strike):
            return price(strike, self.rate)
    for cls in (Own, ByValue):
        p = cls()
        assert p.price(100) == 1.0
        w = weakref.ref(p)
        del p
        gc.collect()
        assert w() is None
    # a bound stops the growth, and still never hits
    class Bounded:
        @lru_cache(maxsize=128)  # noqa: B019
        def price(self, strike):
            return strike
    keep = [Bounded().price(1) for _ in range(300)]
    assert Bounded.price.cache_info().currsize == 128 and Bounded.price.cache_info().hits == 0 and len(keep) == 300


def test_q37():
    import os
    def run(code, seed):
        env = {**os.environ, "PYTHONHASHSEED": str(seed)}
        return subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True).stdout.split()
    prog = (PY / "pp_hashseed.py").read_text()
    out = [run(prog, s) for s in range(6)]
    assert run(prog, 3) == out[3]  # a fixed seed repeats
    winners, sums = {o[0] for o in out}, {o[1] for o in out}
    if is_310:
        assert len(winners) == 4 and sums == {"0.0", "1.0"}
    else:
        assert len(winners) > 1
    ints = "print(list({7, 1000003, 42, 99}))"
    assert len({tuple(run(ints, s)) for s in range(6)}) == 1
    fixed = "s = {'AAA', 'BBB', 'CCC'}; print(max(sorted(s), key=lambda x: (1.0, x)))"
    assert {tuple(run(fixed, s)) for s in range(6)} == {("CCC",)}
    assert list(dict.fromkeys(["z", "a", "m"])) == ["z", "a", "m"]


def test_q38():
    from scipy.stats import spearmanr
    rng = np.random.default_rng(38)
    days, n = 30, 50
    ret = rng.normal(0, 0.01, (days, n))
    price = 100 * np.exp(np.cumsum(ret, axis=0))
    sig = rng.integers(0, 12, (days, n)).astype(float)  # ties on purpose
    sig[rng.random((days, n)) < 0.15] = np.nan
    table = pd.DataFrame({"date": np.repeat(np.arange(days), n), "symbol": np.tile(np.arange(n), days),
                          "price": price.ravel(), "signal": sig.ravel()})
    fast = iv_ic.daily_ic(table.sample(frac=1, random_state=1))
    for d in range(days - 1):
        ok = ~np.isnan(sig[d])
        want = spearmanr(sig[d][ok], price[d + 1][ok] / price[d][ok] - 1).statistic
        assert math.isclose(fast[d], want, abs_tol=1e-9)
    assert len(fast) == days - 1
    # the planted correlation
    rng = np.random.default_rng(2)
    days, n, rho = 200, 500, 0.1
    ret = rng.normal(0, 0.01, (days, n))
    sig = np.full((days, n), np.nan)
    sig[:-1] = rho * ret[1:] / 0.01 + math.sqrt(1 - rho * rho) * rng.normal(0, 1, (days - 1, n))
    planted = pd.DataFrame({"date": np.repeat(np.arange(days), n), "symbol": np.tile(np.arange(n), days),
                            "price": (100 * np.exp(np.cumsum(ret, axis=0))).ravel(), "signal": sig.ravel()})
    ic = iv_ic.daily_ic(planted)
    expected = 6 / math.pi * math.asin(rho / 2)
    assert round(expected, 4) == 0.0955 and round(ic.mean(), 4) == 0.0955 and round(ic.std(), 3) == 0.041
    assert len(ic) == 199 and round(ic.mean() / (ic.std() / math.sqrt(199))) == 33
    assert round(1 / math.sqrt(500), 3) == 0.045
    # the extremes, and no signal at all
    days, n = 6, 40
    px = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.01, (days, n)), axis=0))
    fwd = np.full((days, n), np.nan)
    fwd[:-1] = px[1:] / px[:-1] - 1
    base = pd.DataFrame({"date": np.repeat(np.arange(days), n), "symbol": np.tile(np.arange(n), days), "price": px.ravel()})
    assert np.allclose(iv_ic.daily_ic(base.assign(signal=fwd.ravel())), 1)
    assert np.allclose(iv_ic.daily_ic(base.assign(signal=-fwd.ravel())), -1)
    assert iv_ic.daily_ic(base.assign(signal=1.0)).isna().all()
    # shift on the whole table: the last row of each symbol reads another symbol's first price
    # a slow signal against a five-day target: the plain t-statistic is too large by about sqrt(5)
    from scipy.stats import rankdata
    rng = np.random.default_rng(380)
    tstats = []
    for _ in range(80):
        r = rng.normal(size=(254, 100))
        target = rankdata(np.lib.stride_tricks.sliding_window_view(r, 5, axis=0).sum(axis=2), axis=1)
        sig = rankdata(rng.normal(size=100))
        daily = [np.corrcoef(sig, row)[0, 1] for row in target]
        tstats.append(np.mean(daily) / (np.std(daily, ddof=1) / math.sqrt(len(daily))))
    assert abs(np.mean(tstats)) < 1.0 and 3.5 < np.var(tstats) < 7.5  # one if independent, about five here
    t = pd.DataFrame({"symbol": list("AABB"), "date": [1, 2, 1, 2], "price": [50.0, 50.0, 30.0, 30.0]})
    whole = t.price.shift(-1) / t.price - 1
    assert round(whole[1], 2) == -0.4 and np.isnan(t.groupby("symbol").price.shift(-1)[1])


def test_q39():
    limit = 2**63 - 1
    mult, near = 18 * 10**17 + 1, 18 * 10**17  # a multiplier just above the times, and a time
    assert 4 * mult + near < limit < 5 * mult + near  # symbol 5 plus a time passes the limit, symbol 4 does not
    assert 5 * mult < limit                    # symbol 5 alone still fits, so it is the time that tips it
    key = np.array([4, 5], dtype=np.int64) * np.array([mult], dtype=np.int64) + np.array([near], dtype=np.int64)
    assert key[0] > 0 > key[1]                 # wraps with no error
    with pytest.raises(OverflowError):
        np.array([1], dtype=np.int64) * 10**19  # the stem's multiplier does not fit, and raises
    assert (np.array([5], dtype=np.int64) * (2 * 10**18))[0] < 0  # one that fits wraps, even as a Python int
    base = 1_800_000_000_000_000_000
    rng = np.random.default_rng(39)
    for _ in range(60):
        m, q = rng.integers(0, 40, 2)
        ts, tt = rng.integers(0, 5, m), base + rng.integers(0, 30, m)
        qs, qt = rng.integers(0, 5, q), base + rng.integers(0, 30, q)
        got = iv_asof_numpy.asof(ts, tt, qs, qt)
        for k in range(m):
            best, best_t = -1, -1
            for j in range(q):
                if qs[j] == ts[k] and qt[j] <= tt[k] and qt[j] >= best_t:
                    best, best_t = j, qt[j]
            assert got[k] == best
    # against pandas, on a larger table
    m, q = 20_000, 30_000
    ts, tt = rng.integers(0, 5000, m), base + rng.integers(0, 10**9, m)
    qs, qt = rng.integers(0, 5000, q), base + rng.integers(0, 10**9, q)
    got = iv_asof_numpy.asof(ts, tt, qs, qt)
    left = pd.DataFrame({"t": tt, "s": ts, "row": np.arange(m)}).sort_values("t")
    right = pd.DataFrame({"t": qt, "s": qs, "q": np.arange(q)}).sort_values("t", kind="stable")
    theirs = pd.merge_asof(left, right, on="t", by="s").sort_values("row").q.fillna(-1).astype(int).to_numpy()
    assert (got == theirs).all() and (got == -1).any() and (got >= 0).any()
    empty = iv_asof_numpy.asof(np.array([1]), np.array([base]), np.array([0]), np.array([base]))
    assert empty.tolist() == [-1]  # another symbol's quote is never used
    # the stem gives no dtype for the codes: more than a million distinct times, on narrower codes
    m = q = 600_000
    ts, tt = rng.integers(0, 5000, m), base + rng.integers(0, 10**12, m)
    qs, qt = rng.integers(0, 5000, q), base + rng.integers(0, 10**12, q)
    wide = iv_asof_numpy.asof(ts, tt, qs, qt)
    assert (iv_asof_numpy.asof(ts.astype(np.int32), tt, qs.astype(np.int32), qt) == wide).all()
    assert (iv_asof_numpy.asof(ts.astype(np.int16), tt, qs.astype(np.int16), qt) == wide).all()


def test_q40(monkeypatch):
    m = iv_rolling_beta
    rng = np.random.default_rng(40)
    v = rng.normal(size=53)
    for w in (1, 2, 3, 7, 50, 53, 60):
        want = [v[max(0, i - w + 1) : i + 1].sum() for i in range(53)]
        assert np.allclose(m.window_sum(v, w), want) and np.allclose(m.cumsum_window_sum(v, w), want)
    def slow(x, y, w, min_obs, skip=lambda i: False):
        out = []
        for i in range(len(x)):
            a, b = x[max(0, i - w + 1) : i + 1], y[max(0, i - w + 1) : i + 1]
            ok = ~(np.isnan(a) | np.isnan(b))
            out.append(np.nan if ok.sum() < min_obs or skip(i) else np.polyfit(a[ok], b[ok], 1)[0])
        return np.array(out)
    x, y = rng.normal(0, 0.01, 400), rng.normal(0, 0.01, 400)
    x[rng.random(400) < 0.1] = np.nan
    y[rng.random(400) < 0.1] = np.nan
    assert np.allclose(m.rolling_beta(x, y, 30, 10), slow(x, y, 30, 10), equal_nan=True, rtol=1e-7)
    rng = np.random.default_rng(3)
    x = rng.normal(0, 0.01, 1000)
    y = 2 * x + rng.normal(0, 0.001, 1000)
    x[10] = 1e9
    near = lambda i: 10 <= i < 60  # noqa: E731
    robust, truth = m.rolling_beta(x, y, 50, 10), slow(x, y, 50, 10, skip=near)
    clear = np.arange(60, 1000)
    assert np.allclose(robust[clear], truth[clear], rtol=1e-6) and round(truth[-1], 2) == 2.00
    monkeypatch.setattr(m, "window_sum", m.cumsum_window_sum)
    damaged = m.rolling_beta(x, y, 50, 10)
    monkeypatch.undo()
    assert round(damaged[-1]) == -77
    sxx = m.cumsum_window_sum(x * x, 50)[-1]
    assert sxx == 0.0 and 50 * sxx - m.cumsum_window_sum(x, 50)[-1] ** 2 < 0  # the later squares are rounded away
    assert 2.0e-3 < (x[950:] ** 2).sum() < 8.0e-3
    draws, spreads, corrs = [], [], []
    for seed in range(10):
        g = np.random.default_rng(seed)
        u = g.normal(0, 0.01, 1000)
        v = 2 * u + g.normal(0, 0.001, 1000)
        u[10] = 1e9
        monkeypatch.setattr(m, "window_sum", m.cumsum_window_sum)
        draws.append(m.rolling_beta(u, v, 50, 10)[-1])
        monkeypatch.undo()
        su, sv = pd.Series(u), pd.Series(v)
        spreads.append(su.rolling(50).var().iloc[999])
        corrs.append(su.rolling(50).corr(sv).iloc[999])
    assert max(draws) < -16 and -44_100 < min(draws) < -44_000 and round(max(draws)) == -16
    if pd.__version__ == "2.3.3":
        units = [s / (128 / 49) for s in spreads]
        assert all(abs(k - round(k)) < 1e-3 for k in units) and min(units) < 0 < max(units) and 0 in [round(k) for k in units]
        assert any(np.isnan(k) for k in corrs) and any(k > 1 for k in corrs) and any(0 < k < 0.01 for k in corrs)
    assert math.ulp(1e18) == 128.0
    a, b = pd.Series(x), pd.Series(y)
    if pd.__version__ == "2.3.3":
        assert round(a.rolling(50).var().iloc[999], 1) == -2.6 and np.isnan(a.rolling(50).corr(b).iloc[999])
        assert math.isclose(a.rolling(50).cov(b).iloc[999], a[950:].cov(b[950:]), rel_tol=1e-6)
    assert 0 < a[950:].var() < 1e-3
