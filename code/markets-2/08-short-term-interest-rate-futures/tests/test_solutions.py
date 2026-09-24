"""Numbers gate: every numerical answer printed in Book 2, Chapter 8 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/meetings"))
from firm_meetings import convexity_adjustment, move_probability, strip_rate
from stir_demo import START_RATE, december, path

P = dict(path())
D0, D10, D20 = december(0), december(10), december(20)


def test_text():
    assert round(D0["rate_after"], 3) == 3.986 and round((D0["rate_after"] - D0["rate_in"]) * 100, 1) == 8.8
    assert round(move_probability(P["2026-11"], START_RATE) * 100) == 11
    assert round(31 / 4, 2) == 7.75
    assert round(0.5 * 0.01**2 * 5 * 5.25 * 1e4, 1) == 13.1 and round(0.5 * 0.01**2 * 10 * 10.25 * 1e4, 2) == 51.25
    assert round((D10["probability"] - D0["probability"]) * 100 / 10, 2) == -0.18


def test_exercises():
    assert round(100 - 95.965, 3) == 4.035 and round(3.5 / 0.5) == 7 and 3.5 * 25 * 200 == 17_500
    assert round(2 * 41.67 * 100) == 8_334
    assert round(31 / 3, 1) == 10.3 and round(31 / 3 / 25 * 100) == 41
    assert round(strip_rate([3.95, 4.05, 4.10, 4.12], [91 / 360] * 4), 4) == 4.1178
    a5, a10 = convexity_adjustment(0.01, 5, 5.25) * 1e4, convexity_adjustment(0.01, 10, 10.25) * 1e4
    b5, b10 = convexity_adjustment(0.012, 5, 5.25) * 1e4, convexity_adjustment(0.012, 10, 10.25) * 1e4
    assert (round(b5, 1), round(b10, 1), round(b5 - a5, 1), round(b10 - a10, 2)) == (18.9, 73.8, 5.8, 22.55)


def test_problem():
    r_in = D0["rate_in"]
    assert round(r_in, 4) == 3.8975
    assert round(D0["probability"] * 100, 1) == 35.2 and round(0.25 * 22 / 31, 2) == 0.18
    assert round(D10["probability"] * 100, 1) == 33.4
    assert round(D20["rate_after"], 4) == 3.9765 and round(D20["probability"] * 100, 1) == 31.6
    hold = r_in
    hike = (9 * r_in + 22 * (r_in + 0.25)) / 31
    pnl_hold = (100 - hold - 96.04) * 100 * 41.67 * 1000
    pnl_hike = (100 - hike - 96.04) * 100 * 41.67 * 1000
    assert round(100 - hold, 4) == 96.1025 and round(pnl_hold) == 260_438
    assert round(hike, 4) == 4.0749 and round(100 - hike, 4) == 95.9251 and round(pnl_hike) == -478_869
    p = D0["probability"]
    assert abs((1 - p) * pnl_hold + p * pnl_hike) < 1e-6
    assert round(START_RATE + 0.25, 2) == 4.12
