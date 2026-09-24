"""Tutorial of Book 6, chapter 19: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_xvafund as m


def test_csa_lowers_every_charge_but_margin():
    a, b = m.adjustments(), m.adjustments(csa=True, with_im=True)
    for k in ("cva", "dva", "fca", "fba", "kva"):
        assert b[k] < a[k]
    assert b["mva"] > a["mva"] == 0.0
