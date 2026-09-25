"""Numbers gate: every numerical answer printed in Book 9, chapter 24 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_flowmm import by_type, estimates, markout_curve, policy, summary  # noqa: E402

USD = 100 / 1e6          # a basis point of $1 million, in $ millions


def r(x, d=2):
    return round(float(x), d)


def test_estimates():
    e = estimates()
    assert [r(e[k]["markout"]) for k in ("uninformed", "moderate", "informed")] == [-0.01, 0.84, 2.41]
    assert [r(100 * e[k]["hit"], 0) for k in ("uninformed", "moderate", "informed")] == [80, 43, 8]
    assert r(e["compete_corr"], 3) == 0.998


def test_policies():
    rows = [("flat", 1.0), ("flat", 1.2), ("flat", 1.4), ("flat", 1.6), ("priced", 0.0), ("priced", 0.05)]
    got = [(s["volume"], r(s["capture"] * USD), r(s["marks"] * USD), r(s["hedge_cost"] * USD), r(s["net"] * USD))
           for s in (summary(policy(k, v)) for k, v in rows)]
    assert got == [(74622, 7.46, -1.21, 0.35, 5.9), (64307, 7.72, -0.84, 0.31, 6.57), (53310, 7.46, -0.58, 0.25, 6.63),
                   (42399, 6.78, -0.36, 0.2, 6.23), (62147, 8.53, -0.65, 0.28, 7.6), (61519, 8.35, -0.62, 0.1, 7.63)]
    p0, p5, p20 = policy("priced", 0.0), policy("priced", 0.05), policy("priced", 0.2)
    assert (r(100 * p0["internalised"], 1), r(100 * p5["internalised"], 1)) == (90.8, 96.8)
    assert (r(p0["abs_inventory"]), r(p5["abs_inventory"]), r(p20["abs_inventory"]), r(p20["net"] * USD)) == (
        2.75, 2.18, 1.3, 7.08)
    assert r(100 * p20["internalised"], 1) == 100.0


def test_by_type():
    f, p = by_type(policy("flat", 1.2)), by_type(policy("priced", 0.0))
    got = [(t["trades"], r(t["capture"]), r(t["markout"]), r(t["net"])) for t in (f["uninformed"], p["uninformed"],
                                                                                    f["moderate"], p["moderate"],
                                                                                    f["informed"])]
    assert got == [(53500, 1.2, -0.0, 1.2), (53600, 1.39, -0.0, 1.4), (9869, 1.2, 0.83, 0.37), (8537, 1.25, 0.82, 0.44),
                   (938, 1.2, 2.38, -1.18)]
    assert p["informed"]["trades"] == 10


def test_exercises():
    assert r((1.2 - 0.83) * 100, 0) == 37                                                  # exercise 1
    assert (r(1.2 - 0.05 * 4), r(1.2 + 0.05 * 4)) == (1.0, 1.4)                             # exercise 2
    assert r(1.2 + 0.25 * math.log(0.8 / 0.2)) == 1.55                                     # exercise 3
    s, t = summary(policy("flat", 0.8)), by_type(policy("flat", 0.8))                      # exercise 7
    assert (s["volume"], r(s["marks"] * USD), r(s["net"] * USD), t["informed"]["trades"], r(t["informed"]["net"]),
            r(t["moderate"]["net"])) == (83027, -1.65, 4.6, 3259, -1.72, -0.07)


def test_curve():
    c = markout_curve()
    assert [r(x) for x in c[10][1:]] == [0.71, 2.31]
