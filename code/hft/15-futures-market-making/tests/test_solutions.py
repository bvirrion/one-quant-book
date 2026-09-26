"""Numbers gate: every numerical answer printed in Book 11, chapter 15 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_futures as h  # noqa: E402

fm = h.fm


def r(x, d=0):
    return round(float(x), d)


def test_game():
    g = h.game()
    assert g["fifo"] == 100.0 and r(g["p999"]) == 7907 and r(g["median"]) == 199
    rows = g["rows"]
    assert [r(rows[n]["size"]) for n in (2, 5, 10, 12, 15, 20)] == [110, 143, 230, 298, 619, 5000]
    assert [r(rows[n]["factor"], 1) for n in (2, 5, 10, 12, 15, 20)] == [1.1, 1.4, 2.3, 3.0, 6.2, 50.0]
    assert [r(rows[n]["u_eq"], 1) for n in (2, 5, 10, 12, 15, 20)] == [41.2, 29.6, 19.5, 16.9, 13.9, 12.3]
    assert [r(rows[n]["u_fifo"], 1) for n in (2, 5, 10, 12, 15, 20)] == [41.4, 31.2, 22.3, 20.0, 17.4, 14.3]
    assert [r(rows[n]["big_fill"]) for n in (2, 5, 10, 12, 15, 20)] == [110, 143, 230, 298, 527, 395]
    assert [r(rows[n]["depth_over_mean"], 1) for n in (2, 5, 10, 12)] == [0.5, 1.8, 5.6, 8.8]
    assert (r(rows[15]["depth_over_mean"]), r(rows[20]["depth_over_mean"])) == (23, 245)


def test_implied_and_allocation():
    i = h.implied()
    assert [r(i[lag]["per_1000"], 1) for lag in (1, 5, 10, 20, 30)] == [0.0, 0.9, 5.9, 23.7, 49.7]
    a = h.allocation_example()
    assert a["fifo"] == {"A": 100, "B": 150}
    assert a["pro_rata"] == {"A": 25, "B": 100, "C": 75, "D": 50}
    assert a["top_then_pro_rata"] == {"A": 100, "B": 67, "C": 50, "D": 33}


def test_exercises():
    q = fm.implied_in(fm.Quote(9612, 1, 9613, 1), fm.Quote(9598, 1, 9599, 1))
    assert (q.bid, q.ask) == (13, 15)
    assert min(1000, 2300) * 230 / 2300 == 100
    x = h.riskier()
    assert (x["fifo"], r(x["size"]), r(x["factor"], 1)) == (50.0, 73, 1.5)
