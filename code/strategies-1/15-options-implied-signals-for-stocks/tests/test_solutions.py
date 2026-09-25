"""Numbers gate: every numerical answer printed in Book 8, chapter 15 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_options import book, ic, upcoming  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_ics():
    got = {n: [r(ic(n, h), 3) for h in (1, 5, 20, 60)] for n in ("skew", "spread", "os", "ivrv")}
    assert got == {"skew": [0.004, 0.014, 0.018, 0.012], "spread": [0.005, 0.017, 0.022, 0.015],
                   "os": [0.002, 0.008, 0.01, 0.007], "ivrv": [0.0, 0.001, 0.0, -0.0]}
    ev = {n: [r(ic(n, h, True), 3) for h in (1, 5, 20, 60)] for n in ("skew", "spread", "os")}
    assert ev == {"skew": [0.026, 0.085, 0.111, 0.082], "spread": [0.03, 0.101, 0.129, 0.094],
                  "os": [0.015, 0.047, 0.061, 0.045]}
    assert r(100 * upcoming().mean(), 1) == 11.7


def test_books():
    f = lambda b: (r(b["sr_gross"]), r(b["sr_net"]), r(100 * b["ret_gross"], 1), r(100 * b["ret_net"], 1))  # noqa: E731
    assert f(book("skew")) == (3.17, -0.93, 7.0, -2.3)
    assert f(book("spread")) == (3.67, -0.35, 8.5, -0.9)
    assert f(book("os")) == (2.14, -1.7, 4.9, -4.4)
    assert f(book("skew", True)) == (6.59, 4.58, 32.3, 23.0)
    assert f(book("spread", True)) == (8.07, 6.12, 41.2, 31.9)
    assert f(book("os", True)) == (3.57, 1.75, 18.3, 9.1)


def test_exercises():
    assert r(0.003 * 1.5 * 2, 4) == 0.009 and r(0.003 * 2, 3) == 0.006
    assert r(0.0034 * 52 * 100, 1) == 17.7 and r(0.005 * 52 * 100, 0) == 26
