"""Numbers gate: every numerical answer printed in Book 7, chapter 18 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_lobreplay import LATENCIES, bar_quoter_level3, impact_bound, see_or_act, tape, touch_grid


def test_touch_grid():
    assert len(tape(31, 3600.0).msgs) == 129_303
    g = touch_grid()
    row = lambda m, k: [g[(m, lat)][k] for lat in LATENCIES]  # noqa: E731
    assert [round(x) for x in row("front", "pnl")] == [1106, 778, 672, 498, 192]
    assert [round(100 * x) for x in row("front", "share")] == [61, 48, 43, 28, 11]
    assert [round(x) for x in row("fifo", "pnl")] == [-76, -94, -89, -146, -8]
    assert [round(x) for x in row("fifo", "lots")] == [522, 505, 470, 350, 182]
    assert [round(x, 3) for x in row("fifo", "markout")] == [0.008, -0.001, -0.025, -0.1, -0.115]
    assert [round(x) for x in row("prob", "pnl")] == [-49, -42, -41, -26, 33]
    assert round(g[("front", 0.0)]["lots"]) == 3195 and round(100 * g[("fifo", 0.0)]["share"]) == 10
    assert round(g[("prob", 0.0)]["lots"]) == 499 and round(g[("front", 0.0)]["markout"], 2) == 0.39
    assert (round(impact_bound(g[("fifo", 0.0)])), round(impact_bound(g[("fifo", 5.0)]))) == (26, 9)


def test_bar_quoter_and_exercises():
    b = bar_quoter_level3()
    lots = np.mean([r["lots"] for r in b])
    assert (round(lots), round(100 * lots / np.mean([r["orders"] for r in b])), round(np.mean([r["pnl"] for r in b])),
            round(np.mean([r["markout"] for r in b]), 2)) == (344, 47, -239, -0.77)
    s = see_or_act(1.0)
    assert (round(s["act late"]["lots"]), round(s["act late"]["markout"], 3), round(s["act late"]["pnl"])) == (376, -0.075, -133)
    assert (round(s["see late"]["lots"]), round(s["see late"]["markout"], 3), round(s["see late"]["pnl"])) == (416, -0.132, -173)
    assert (600 - 400 * 600 / 800, 200 - 400 * 200 / 800) == (300.0, 100.0)
    assert 522 * 100 * 0.10 / 2 == 2610
