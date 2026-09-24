"""Tutorial of Book 6, chapter 18: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_cva as m


def test_orderings():
    a, c = m.adjustments(), m.adjustments(csa=True)
    assert a["cva_bil"] < a["cva"] and a["dva_bil"] < a["dva"] and c["cva"] < a["cva"]
    d = [x for _, x in m.dva_shift()]
    assert all(b > a for a, b in zip(d, d[1:], strict=False))
