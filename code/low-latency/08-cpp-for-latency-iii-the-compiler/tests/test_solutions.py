"""Numbers gate and compiler properties, Book 13 chapter 8."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_flags as fl  # noqa: E402
import ll_ub  # noqa: E402


def near(x, want, rel=0.25):
    return abs(x - want) <= rel * want


def test_ub_assembly_with_the_installed_compiler():
    plus = ll_ub.body("plus_one_greater", "-O2")
    assert not any(w in " ".join(plus) for w in ("cmp", "add", "lea")) and "mov\teax, 1" in plus[0]
    assert not any(w in " ".join(ll_ub.body("first_then_check", "-O2")) for w in ("test", "cmp"))
    alias = ll_ub.body("alias", "-O2")
    assert "mov\teax, 1" in " ".join(alias)                              # returns 1 without reloading *i
    printed = (HERE / "cpp/asm/plus_one_greater_O0.s").read_text()
    assert "mov\teax, 1" in printed and "add" not in printed             # folded even at -O0 (g++ 11.4 listing)


def test_sanitiser():
    assert "signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'" in ll_ub.ubsan(2147483647)
    assert ll_ub.ubsan(5) == ""


def test_measured_matrix():
    d = fl.rows("measured_flags.csv")
    assert all(r["ok"] == "1" for r in d.values())                       # every set gave the -O2 checksum
    sp = {k: float(r["speedup"]) for k, r in d.items()}
    assert sp["O3"] > 3 and 2.2 < sp["O2 PGO"] < 3 and 4.5 < sp["O3 native LTO PGO"] < 5.0   # three, 2.5, nearly five
    assert [round(sp[k], 1) for k in ("O3", "O2 PGO", "O3 native LTO PGO")] == [3.7, 2.6, 4.8]
    assert [round(sp[k], 2) for k in ("O0", "O2 native", "O2 LTO")] == [0.13, 1.02, 1.02]
    assert near(sp["O2 native"], 1, 0.1) and near(sp["O2 LTO"], 1, 0.1) and sp["O0"] < 0.2
    ns = {k: float(r["ns"]) for k, r in d.items()}
    assert [round(ns[k] * 5, -1 if k == "O0" else 0) for k in ("O0", "O2", "O3")] == [460, 58, 16]  # exercise 1, ms/s
    assert [round(ns["O0"]), round(ns["O2"], 1), round(ns["O3"], 1)] == [92, 11.6, 3.1]
    f = fl.rows("measured_fastmath.csv")
    assert f["O2"]["checksum"] == f["O3 native"]["checksum"] == "14.4036837"
    assert f["O3 native fast-math"]["ok"] == "0" and 6 < float(f["O3 native fast-math"]["speedup"]) < 9  # seven times
    exact = fl.harmonic(2**20)
    assert round(exact, 2) == 14.44
    assert abs(float(f["O3 native fast-math"]["checksum"]) - exact) < abs(float(f["O2"]["checksum"]) - exact) / 20
