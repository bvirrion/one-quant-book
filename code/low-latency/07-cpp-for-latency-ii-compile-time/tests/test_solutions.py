"""Numbers gate and assembly properties, Book 13 chapter 7."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_asm  # noqa: E402
import ll_compile as c  # noqa: E402


def near(x, want, rel=0.25):
    return abs(x - want) <= rel * want


def test_assembly_properties_with_the_installed_compiler():
    static, dynamic = ll_asm.body("run_static"), ll_asm.body("run_dynamic")
    assert ll_asm.calls(static) == []                    # every stage inlined, whatever the g++ version
    assert any("call" in x and "[" in x for x in ll_asm.calls(dynamic))     # an indirect call per stage


def test_printed_listing():
    printed = (HERE / "cpp/asm/run_static.s").read_text().splitlines()
    assert len([x for x in printed if not x.startswith(".L")]) == 13 and ll_asm.calls(printed) == []
    assert "call\t[QWORD PTR 16[rax]]" in (HERE / "cpp/asm/run_dynamic.s").read_text()


def test_measured_and_arithmetic():
    d = c.dispatch()
    v1, vm = d["virtual"]
    c1, cm = d["CRTP"]
    assert c1 < d["variant"][0] < v1 and cm < d["variant"][1] < vm       # ordering only
    assert near(c1, 0.5, 0.4) and near(v1 / c1, 3.7, 0.3)                 # half a ns; about four times
    assert v1 / c1 > vm / cm                                              # the gap narrows on the mix
    st, dy = d["pipeline static"][0], d["pipeline dynamic"][0]
    assert near(st, 1.0, 0.35) and near(dy, 7.0, 0.3)                     # about one and seven
    assert near((dy - st) * 5e6 / 1e6, 30.6, 0.3)                         # exercise 2: ms per second
    p = c.pow10(18)
    assert 250 * p[2] == 25_000 and 2500 // p[2] == 25 and p[18] == 10**18  # exercise 3
    assert 3 * 2 == 6                                                     # problem 11
