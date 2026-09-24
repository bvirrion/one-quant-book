"""Tutorial of Book 6, chapter 6: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_cms as m


def test_adjustments_grow_with_expiry_and_the_smile_adds():
    rows = m.cms_table()
    assert all(b[2] > a[2] and b[3] > a[3] for a, b in zip(rows, rows[1:], strict=False))
    assert all(r[3] > r[2] for r in rows)
