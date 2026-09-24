"""Numbers gate: every numerical answer printed in Book 6, chapter 18 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_cva as m
from firm_cva import cva, discounted_profiles
from firm_exposure import exposure

A = m.adjustments()
C = m.adjustments(csa=True)
CS = m.cs01()
W = dict(m.wrong_way())
S = dict(m.dva_shift((0, 50)))


def standalone():
    d, v = m.data(), m.ex.values()
    t = d["t"][:-1]
    out = []
    for k in ("swap", "xccy"):
        dee, _ = discounted_profiles(exposure(v[k])[:, :-1], d["D"][:, :-1])
        out.append(cva(dee, t, d["cpty"], m.R))
    return out


def test_text():
    assert round(100 * (1 - m.data()["cpty"].survival(10)), 1) == 26.4
    assert round(A["cva"]) == 891_342
    sw, xc = standalone()
    assert (round(sw), round(xc)) == (288_250, 768_334) and round(1 - A["cva"] / (sw + xc), 2) == 0.16
    assert round(m.annuity10(), 2) == 7.45 and round(m.running_bp(), 1) == 12.0
    assert round(A["dva"]) == 1_055_437
    assert (round(A["cva_bil"]), round(A["dva_bil"]), round(A["bcva"])) == (832_416, 896_328, -63_912)
    assert (round(C["cva"]), round(C["dva"])) == (122_340, 70_490)
    assert (round(W[0.0]), round(W[2.0]), round(W[5.0])) == (766_532, 1_108_459, 1_521_524)
    assert [round(x) for x in CS] == [-235, -165, -141, -22, 125, 4_693] and round(sum(CS)) == 4_254
    assert round(sum(CS) / (m.annuity10() * 1e-4) / 1e6, 1) == 5.7


def test_exercises():
    assert round(0.6 * 2e6 * (1 - math.exp(-0.1))) == 114_195
    ps = m.ex.profile_set()
    assert round(ps["net"][1]["epe_life"] * 0.0175 * m.annuity10()) == 840_420
    assert round(1 - C["cva"] / A["cva"], 2) == 0.86 and round(1 - C["dva"] / A["dva"], 2) == 0.93
    w = m.wrong_way(tuple(range(11)))
    assert max(w, key=lambda x: x[1])[0] == 7


def test_problem():
    assert (round(S[0]), round(S[50]), round(S[50] - S[0])) == (1_055_437, 1_513_008, 457_571)
    assert round(500 * (S[50] - S[0]) / 1e6) == 229
