"""Numbers gate for Book 18, chapter 24: every output-prediction snippet is run with the pinned interpreter and its
output asserted; the coding answers are tested against direct computations."""
import pathlib
import random
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_py import (
    OrderKey,
    large_fills,
    notional_by_symbol,
    read_fills,
    rolling_mean_loop,
    rolling_mean_vec,
    temporary_limit,
)

HERE = pathlib.Path(__file__).resolve().parents[1] / "python"

OUTPUT = {
    "iv_snip_mutable_default": "[1]\n[1, 2]\n[3]\n",
    "iv_snip_late_binding": "[20, 20, 20]\n[0, 10, 20]\n",
    "iv_snip_identity": "True True\nTrue False\n",  # CPython caches small ints (-5..256): an implementation detail
    "iv_snip_generator_twice": "5\n0\n",
    "iv_snip_dict_mutation": "RuntimeError: dictionary changed size during iteration\n{'B': 5}\n",
    "iv_snip_views": "[100.   0. 102. 103.]\nTrue False\n",
    "iv_snip_float_sum": "False 0.9999999999999999\nTrue\n",
    "iv_snip_chained": "[0, 0, 0]\nTrue\n[0, 1, 0]\n",  # pandas 2.3 without copy-on-write
}


@pytest.mark.parametrize("name", sorted(OUTPUT))
def test_output_prediction(name):
    r = subprocess.run([sys.executable, str(HERE / "snippets" / f"{name}.py")], capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout == OUTPUT[name]


def test_pipeline(tmp_path):
    rng = random.Random(0)
    path = tmp_path / "fills.csv"
    rows = [(rng.choice("ABC"), rng.randint(-500, 500), round(rng.uniform(10, 200), 2)) for _ in range(5000)]
    path.write_text("sym,qty,px\n" + "".join(f"{s},{q},{p}\n" for s, q, p in rows), encoding="ascii")
    gen = read_fills(path)
    assert iter(gen) is gen  # a generator, not a list
    got = notional_by_symbol(large_fills(gen, 20_000))
    want = {}
    for s, q, p in rows:
        if abs(q) * p >= 20_000:
            want[s] = want.get(s, 0.0) + q * p
    assert got.keys() == want.keys() and all(abs(got[k] - want[k]) < 1e-6 for k in got)


def test_context_manager():
    limits = {"gross": 100}
    with temporary_limit(limits, "gross", 50):
        assert limits["gross"] == 50
    assert limits["gross"] == 100
    with pytest.raises(ValueError):
        with temporary_limit(limits, "gross", 10):
            raise ValueError("breach")
    assert limits["gross"] == 100


def test_vectorised_rolling_mean():
    for seed in range(50):
        rng = np.random.default_rng(seed)
        x = rng.normal(size=rng.integers(5, 200)).tolist()
        k = int(rng.integers(1, 5))
        assert np.allclose(rolling_mean_vec(x, k), rolling_mean_loop(x, k))


def test_value_type():
    d = {OrderKey("X", 7): "filled"}
    assert d[OrderKey("X", 7)] == "filled"
    with pytest.raises(AttributeError):
        OrderKey("X", 7).client_order_id = 8  # frozen
