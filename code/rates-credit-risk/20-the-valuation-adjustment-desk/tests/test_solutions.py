"""Numbers gate: every numerical answer printed in Book 6, chapter 20 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_xvadesk as m

INC = m.incremental_table()
A = m.allocation()
P = m.proxy()
Q = m.twenty_year_quote()
B = m.twenty_year_quote(("BBB", "industrials", "US"), 0.03)


def test_text():
    assert round(INC["pay"]["base"]) == 891_342
    assert (round(INC["pay"]["standalone"]), round(INC["pay"]["with"]), round(INC["pay"]["incremental"])) == (
        37_061, 869_582, -21_761)
    assert (round(INC["receive"]["standalone"]), round(INC["receive"]["incremental"])) == (30_742, 22_784)
    assert [round(x) for x in A["euler"]] == [160_167, 731_175]
    assert [round(x) for x in A["standalone"]] == [288_250, 768_334]
    assert len(m.PEERS) == 18 and round(100 * P["rmse"], 1) == 1.3 and round(1e4 * P["spread"], 1) == 337.5
    c = m.proxy_curve()
    assert (round(1e4 * c[0]), round(1e4 * c[-1])) == (154, 338)
    q = m.quote_data()
    assert round(100 * Q["k"], 2) == 4.11 and round(q["ee"].max() / 1e6, 2) == 5.65 and round(q["t"][q["ee"].argmax()]) == 5
    assert (round(Q["cva"]), round(Q["fca"]), round(Q["kva"])) == (1_649_494, 343_872, 3_141_826)
    assert round(m.annuity(), 2) == 13.67
    assert (round(Q["cva_bp"], 1), round(Q["fca_bp"], 1), round(Q["kva_bp"], 1), round(Q["total_bp"], 1)) == (
        12.1, 2.5, 23.0, 37.6)


def test_exercises():
    assert round(1e4 * 1e6 / (1e8 * m.annuity()), 1) == 7.3
    assert round(Q["cs01"]) == 2_385 and round(Q["hedge_notional"] / 1e6, 2) == 3.55


def test_problem():
    assert round(Q["hedgeable_share"], 2) == 0.32
    assert (round(B["total_bp"], 1), round(B["cva_bp"], 1), round(B["fca_bp"], 1), round(B["kva_bp"], 1)) == (
        26.2, 7.2, 3.1, 15.8)
