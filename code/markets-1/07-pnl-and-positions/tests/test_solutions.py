"""Numbers gate: every numerical answer printed in the Chapter 7 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from pnl_day import U, explain, fifo, fx_split, replay, three_numbers, units

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/pnl"))
from firm_pnl import BUY, SELL, Position


def run(fills, start=None):
    p = Position()
    if start:
        p.on_fill(BUY, start[0], units(start[1]))
    track = []
    for side, qty, px in fills:
        p.on_fill(side, qty, units(px))
        track.append((p.quantity, round(p.avg_cost / U, 4), round(p.realised / U, 2)))
    return p, track


def test_text():
    assert three_numbers() == {"trader": 40_000.0, "risk": 31_000.0, "finance": 27_000.0}
    p = replay()
    assert p.cash / U == -1_469_000 and round(p.realised / U) == 26_406 and round(p.avg_cost / U, 3) == 49.847
    assert round(p.unrealised(units(50.0)) / U) == 4_594
    r, u = fifo()
    assert round(r) == 28_750 and round(u) == 2_250
    assert 300 + 200 == 500 and 300 - 200 == 100
    s = fx_split(10_000, 40.0, 41.0, 1.10, 1.08)
    assert [round(s[k]) for k in ("price", "currency", "cross", "total")] == [11_000, -8_000, -200, 2_800]
    e = explain(30_000, 50.00, 50.40, [("t", -1, 10_000, 50.35, 0), ("t", 1, 5_000, 50.10, 0)], 900, 650)
    assert [round(v) for v in e.values()] == [12_000, 1_000, -900, -650, 11_450]


def test_exercises():
    assert 40_000 * 25 + 10_000 * 120 + 30_000 * 50 == 3_700_000                      # 1
    assert 40_000 * 25 + 10_000 * 120 - 30_000 * 50 == 700_000
    p, tr = run([(BUY, 500, 20.0), (BUY, 300, 20.4), (SELL, 600, 20.5)])              # 2, 3
    assert tr == [(500, 20.0, 0.0), (800, 20.15, 0.0), (200, 20.15, 210.0)]
    assert p.unrealised(units(20.30)) / U == pytest.approx(30) and p.cash / U == -3_820
    assert p.total(units(20.30)) / U == 240
    p, tr = run([(SELL, 1000, 80.0), (SELL, 1000, 81.0), (BUY, 3000, 79.5)])          # 4, 7
    assert tr == [(-1000, 80.0, 0.0), (-2000, 80.5, 0.0), (1000, 79.5, 2000.0)]
    assert p.total(units(79.8)) / U == 2_300
    s = fx_split(50_000, 200, 190, 0.80, 0.84)                                        # 5
    assert [round(s[k]) for k in ("price", "currency", "cross", "total")] == [-400_000, 400_000, -20_000, -20_000]
    carried = -20_000 * (29.70 - 30.00)                                               # 6
    new = 8_000 * (29.70 - 29.60) - 5_000 * (29.70 - 29.90)
    assert round(carried) == 6_000 and round(new) == 1_800 and round(carried + new - 260 - 120 + 65) == 7_485


def test_problem():
    fills = [(SELL, 7_000, 84.60), (SELL, 9_000, 84.90), (BUY, 6_000, 84.20), (BUY, 10_000, 83.70)]
    p, tr = run(fills, start=(12_000, 82.50))
    assert [t[0] for t in tr] == [5_000, -4_000, 2_000, 12_000]
    cash = sum(-(1 if s == BUY else -1) * q * px for s, q, px in fills)
    assert round(cash) == 14_100
    fees = 32_000 * 0.0012
    assert fees == pytest.approx(38.40)
    day = {m: round(cash + 12_000 * m - 12_000 * 84.00) for m in (83.55, 83.75, 83.76, 83.70)}
    assert day == {83.55: 8_700, 83.75: 11_100, 83.76: 11_220, 83.70: 10_500}
    carried = 12_000 * (83.76 - 84.00)
    new = [(1 if s == BUY else -1) * q * (83.76 - px) for s, q, px in fills]
    assert round(carried) == -2_880 and [round(x) for x in new] == [5_880, 10_260, -2_640, 600]
    assert round(carried + sum(new) - fees - 310, 2) == 10_871.60
    assert tr == [(5_000, 82.5, 14_700.0), (-4_000, 84.9, 26_700.0), (2_000, 84.2, 29_500.0),
                  (12_000, 83.7833, 29_500.0)]
    unreal = p.unrealised(units(83.76)) / U
    assert round(unreal) == -280 and round(29_500 + unreal - 12_000 * 1.5) == 11_220
