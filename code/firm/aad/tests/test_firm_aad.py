"""Acceptance tests of firm.aad (Python reference)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_aad as ad  # noqa: E402


def F(z):
    """The cross-language test function (also in cpp/firm_aad_test.cpp and rust/src/lib.rs)."""
    n = len(z)
    D = [ad.exp(-(z[i] * (0.075 * (i + 1)))) for i in range(n)]
    tot = 0.0
    for i in range(n):
        w = 1.0 + (i % 7)
        tot = tot + D[i] * w
        if i > 0:
            tot = tot + ad.ncdf((ad.log(D[i - 1] / D[i]) - 0.002) / 0.05) * w
    return tot


def test_elementary_rules():
    val, g, st = ad.gradient(lambda v: v[0] * v[1] + ad.exp(v[0]) / v[1] - ad.sqrt(v[1]) + 3.0 - v[0], [0.5, 2.0])
    x, y = 0.5, 2.0
    assert abs(val - (x * y + math.exp(x) / y - math.sqrt(y) + 3 - x)) < 1e-15
    assert abs(g[0] - (y + math.exp(x) / y - 1)) < 1e-14 and abs(g[1] - (x - math.exp(x) / y**2 - 0.5 / math.sqrt(y))) < 1e-14
    assert st == {"ops": 8, "partials": 13, "nodes": 10}
    _, g2, _ = ad.gradient(lambda v: ad.ncdf(v[0]) + ad.maximum(v[1], 1.0) + 2.0 / v[0] + (1.0 - v[1]) + (-v[0]), [0.3, 1.5])
    assert abs(g2[0] - (math.exp(-0.045) / math.sqrt(2 * math.pi) - 2 / 0.09 - 1)) < 1e-12 and g2[1] == 0.0


def test_cross_language_reference_and_modes():
    z = [0.03 + 0.0001 * i for i in range(400)]
    val, g, st = ad.gradient(F, z)
    assert val == 1643.8656977694293 or abs(val - 1643.8656977694293) < 1e-9
    assert (abs(g[0] + 1.2716414715908044) < 1e-10, abs(g[17] + 15.944508608229377) < 1e-10,
            abs(g[399] - 233.82677751949) < 1e-9) == (True, True, True)
    assert st["ops"] == 4793 and st["partials"] == 5990
    fw = ad.forward_gradient(F, z)
    assert max(abs(a - b) for a, b in zip(g, fw, strict=True)) < 1e-11
    sub = z[:30]
    bump = ad.bump_gradient(F, sub, h=1e-6)
    _, gs, _ = ad.gradient(F, sub)
    assert max(abs(a - b) / (1 + abs(b)) for a, b in zip(bump, gs, strict=True)) < 1e-6
    one = ad.bump_gradient(F, sub, h=1e-7, central=False)
    assert max(abs(a - b) / (1 + abs(b)) for a, b in zip(one, gs, strict=True)) < 1e-4


def test_checkpointing_equals_full_tape():
    def step(x, th):
        return x + (th - x) * 0.01 + ad.exp(-(x * x)) * 0.001

    def loss(x):
        return x * x
    tape = ad.Tape()
    x0, th = tape.var(0.2), tape.var(0.9)
    y = x0
    for _ in range(500):
        y = step(y, th)
    bar = tape.adjoints(loss(y))
    for every in (1, 7, 50, 500):
        cp = ad.checkpointed_gradient(step, 0.2, 0.9, 500, loss, every)
        assert abs(cp["d_x0"] - bar[x0.idx]) < 1e-13 and abs(cp["d_theta"] - bar[th.idx]) < 1e-12
    assert ad.checkpointed_gradient(step, 0.2, 0.9, 500, loss, 25)["peak_states"] == 21 + 25
