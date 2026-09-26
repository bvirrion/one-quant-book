"""Numbers gate, Book 13 chapter 14."""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_simd as s  # noqa: E402
import ll_vecreport as vr  # noqa: E402


def swar(digits):
    v = int.from_bytes(digits.encode(), "little") - 0x3030303030303030
    v = (v * 10 + (v >> 8)) & 0x00FF00FF00FF00FF
    pairs = [(v >> (16 * k)) & 0xFFFF for k in range(4)]
    v = (v * 100 + (v >> 16)) & 0x0000FFFF0000FFFF
    quads = [(v >> (32 * k)) & 0xFFFFFFFF for k in range(2)]
    v = (v * 10000 + (v >> 32)) & 0xFFFFFFFF
    return pairs, quads, v


def test_exercises():
    assert (s.lanes(32, 8), s.lanes(32, 4), s.lanes(32, 1)) == (4, 8, 32)
    assert divmod(1500, 32) == (46, 28)                                                  # 46 full + 1 overlapping
    assert [i for i in range(32) if 0x00041010 >> i & 1] == [4, 12, 18]                 # exercise 2
    assert swar("20260925") == ([20, 26, 9, 25], [2026, 925], 20260925)                  # exercise 3
    assert 70 - 32 == 38 and 64 - 38 == 26                                               # exercise 4
    assert s.traffic(1) == (88, 48)


def test_measured_scan_and_problem():
    per = {m: float(next(r for r in s.read("measured_scan.csv") if r["bytes"] == "4096")[m]) / 4096
           for m in ("scalar", "sse2", "avx2")}
    assert 0.15 < per["scalar"] < 0.4 and 0.012 < per["sse2"] < 0.04 and 0.006 < per["avx2"] < 0.025
    assert round(per["scalar"], 2) == 0.22 and round(per["sse2"], 3) == 0.024 and round(per["avx2"], 3) == 0.013
    assert 50 < s.bytes_per_ns("avx2") < 120 and 2.5 < s.bytes_per_ns("scalar") < 6                   # ~80 vs ~4
    assert round(s.bytes_per_ns("avx2")) == 79 and round(s.bytes_per_ns("avx2") / s.bytes_per_ns("scalar")) == 18
    a, b = s.fit("avx2", 32)
    assert 0.2 < a < 1 and round(a, 1) == 0.3 and round(b, 4) == 0.0125
    assert 1 < s.breakeven() < 16 and round(s.breakeven()) == 2 and round(s.breakeven("sse2")) == 8


def test_measured_split_parse():
    sp = {r["method"]: r for r in s.read("measured_split.csv")}
    sc, vx = float(sp["scalar"]["ns_per_message"]), float(sp["avx2"]["ns_per_message"])
    assert sp["scalar"]["fields"] == "16" and sp["scalar"]["mean_bytes"] == "159.0"
    assert 50 < sc < 250 and 5 < vx < 40 and sc / vx > 5                                   # ~108 vs ~11
    assert round(sc) == 95 and round(vx) == 11 and round(sc / vx) == 9
    assert round(sc * 200 / 159) == 120 and round(vx * 200 / 159) == 14                   # problem 5
    assert round(sc * 200 / 159 * 2e5 / 1e6) == 24 and round(vx * 200 / 159 * 2e5 / 1e5) == 28   # problem 6
    assert round((sc - vx) * 200 / 159) == 106
    p = {r["key"]: float(r["ns"]) for r in s.read("measured_parse.csv")}
    assert p["sse"] <= p["swar"] < p["scalar"] < p["fromchars"] < p["strtod"]
    assert (round(p["scalar"], 1), round(p["swar"], 1), round(p["sse"], 1)) == (2.0, 1.0, 0.7)
    assert round(p["fromchars"]) == 5 and round(p["fixed"]) == 7 and round(p["strtod"]) == 43
    assert (round(p["strtod"], 1), round(p["fixed"], 1)) == (42.6, 6.6)
    assert round(4 * (p["strtod"] - p["fixed"])) == 144 and 4 * (p["strtod"] - p["fixed"]) > (sc - vx) * 200 / 159


def test_measured_reval():
    r = {x["key"]: {k: float(v) for k, v in x.items() if k != "key"} for x in s.read("measured_reval.csv")}
    for k in r:
        assert 0.5 < r[k]["rows_1k"] < 1.2                                                # ~0.8 whatever the flags
        assert 2 < r[k]["rows_1m"] / r[k]["cols_1m"] < 5                                 # about three times
    assert abs(r["O2"]["cols_1k"] / r["O2"]["rows_1k"] - 1) < 0.25                        # -O2: no vectorisation
    assert 0.35 < r["O3"]["cols_1k"] / r["O2"]["cols_1k"] < 0.7                            # half
    assert 0.15 < r["O3avx2"]["cols_1k"] / r["O2"]["cols_1k"] < 0.4                        # a quarter


def test_vectorisation_report():
    major, body = vr.lines()
    text = "\n".join(body)
    committed = (HERE / "cpp/vecreport/gxx11.txt").read_text().strip()
    if major == 11:
        assert text == committed
    o3 = [x for x in body if x.startswith("-O3  ")]
    assert any("line 13: optimized: loop vectorized" in x for x in o3)                  # columns vectorised
    assert not any("line 20: optimized" in x or "line 21: optimized" in x for x in o3)   # records not
    assert any("line 34: optimized: loop vectorized" in x for x in o3)                  # integer sum
    if major < 14:
        assert any("line 27: missed" in x for x in o3)                                  # early exit
    if major < 12:
        assert body[1].startswith("-O2") and "no loop vectorised" in body[1]


def test_sum_doubles_keeps_its_order():
    """GCC reports the double sum 'vectorized' but the assembly adds one element at a time (scalar addsd)."""
    cmd = ["g++", "-std=c++20", "-O3", "-S", "-masm=intel", "-I", str(HERE / "cpp"), str(HERE / "cpp/ll_vecdemo.cpp"),
           "-o", "-"]
    asm = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    body = asm[asm.index("_Z11sum_doublesPKdm:"):]
    body = body[:body.index(".cfi_endproc")]
    assert "addsd" in body and "addpd" not in body
