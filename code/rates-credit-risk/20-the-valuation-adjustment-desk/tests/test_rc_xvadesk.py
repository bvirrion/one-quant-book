"""Tutorial of Book 6, chapter 20: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_xvadesk as m


def test_allocation_adds_up_and_offsetting_trade_earns_a_rebate():
    a = m.allocation()
    assert abs(sum(a["euler"]) - a["total"]) < 1e-6 * a["total"]
    assert m.incremental_table()["pay"]["incremental"] < 0 < m.incremental_table()["receive"]["incremental"]
