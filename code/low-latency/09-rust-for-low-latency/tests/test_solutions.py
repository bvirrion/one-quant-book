"""Numbers gate and compiler properties, Book 13 chapter 9 (allocation counts are asserted by the Rust tests)."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_rustasm as ra  # noqa: E402

FIG = HERE.parents[2] / "figdata/low-latency/09-rust-for-low-latency"


def rows(name):
    with open(FIG / name, newline="") as f:
        return {r["task"]: (float(r["cpp"]), float(r["rust"])) for r in csv.DictReader(f)}


def test_rust_assembly_with_the_installed_rustc():
    counted, checked = ra.body("sum_counted"), ra.body("get_checked")
    assert not any("panic" in x for x in counted)                       # bounds checks eliminated
    assert any("paddq" in x or "vpaddq" in x for x in counted)          # and the loop vectorised
    assert any("panic_bounds_check" in x for x in checked) and any("cmp" in x for x in checked)


def test_printed_listings():
    s = (HERE / "rust/asm/sum_counted.s").read_text()
    assert "panic" not in s and len(s.splitlines()) == 40 and s.count("paddq") >= 2
    assert "panic_bounds_check" in (HERE / "rust/asm/get_checked.s").read_text()


def test_measured():
    dec = rows("measured_decode.csv")["decode"]
    assert 8 < dec[0] < 14 and 8 < dec[1] < 15 and 0.8 < dec[1] / dec[0] < 1.25    # about eleven, within a fifth
    loops = rows("measured_loops.csv")
    assert loops["counted loop"][1] < loops["counted loop"][0]                     # LLVM vectorised, g++ -O2 did not
    for lang in (0, 1):
        c, u = loops["gather checked"][lang], loops["gather unchecked"][lang]
        assert abs(c - u) / u < 0.15                                                # the same within noise
