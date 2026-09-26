"""Numbers gate: every numerical answer printed in Book 11, chapter 14 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_dr as h  # noqa: E402

fd = h.fd


def r(x, d=0):
    return round(float(x), d)


def test_errors():
    e = h.errors()
    assert r(e["home"]["open"], 1) == 2.0 and (r(e["proxy"]["closed"]), r(e["home"]["closed"])) == (74, 94)
    assert (r(e["proxy"]["end"]), r(e["home"]["end"])) == (109, 137)
    half = h.errors(0.006)
    assert (r(half["proxy"]["closed"]), r(half["proxy"]["end"]), r(half["home"]["closed"])) == (38, 57, 70)


def test_overlap_and_threshold():
    g = h.overlap_gaps()
    assert r(g["sd"], 1) == 4.5 and r(100 * g["over"], 1) == 2.7
    assert r(h.threshold(), 1) == 28.8


def test_exercises():
    assert fd.dr_fair(10.0, 2.0, 1.25) == 25.0 and r(fd.closed_fair(10.0, 2.0, 1.25, 0.01, 1.2), 2) == 25.30
    act, edge = fd.conversion_edge(25.2, 10.0, 2.0, 1.25, 0.05, 6.0)
    assert act == "issue" and r(edge, 3) == 0.128
    assert r(2 * 8.00 * 1.27, 2) == 20.32
