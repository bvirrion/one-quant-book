"""Chapter 21 of Book 2: the spread measures and data behave as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from credit_demo import callable_oas, load_hqm, measures


def test_spread_ordering():
    m = measures()
    assert m["g"] < m["z"] < m["i"] < m["asw"]
    assert 0 < callable_oas()["oas"] < m["z"]


def test_hqm_data():
    rows = load_hqm()
    assert len(rows) == 512 and rows[0][0] == "1984-01-01"
    peak = max(rows, key=lambda r: r[1] - r[2])
    assert peak[0] == "2008-10-01"
