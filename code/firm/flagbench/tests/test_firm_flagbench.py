import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_flagbench as fb

PROG = r"""
#include <chrono>
#include <cstdio>
#include <vector>
int main() {
    std::vector<float> v(200000);
    for (std::size_t i = 0; i < v.size(); ++i) v[i] = 1.0f / static_cast<float>(i + 1);
    const auto t0 = std::chrono::steady_clock::now();
    float s = 0.0f;
    for (float x : v) s += x;                         // order-dependent in floating point
    long long k = 0;
    for (std::size_t i = 0; i < v.size(); ++i) k += static_cast<long long>(i % 7);
    const double ns = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count();
    std::printf("%.9g %lld\n%.3f\n", s, k, ns / v.size());
}
"""


def test_matrix_verifies_outputs(tmp_path):
    src = tmp_path / "p.cpp"
    src.write_text(PROG)
    sets = [fb.FlagSet("O2", ("-O2",)), fb.FlagSet("O0", ("-O0",)), fb.FlagSet("O2 PGO", ("-O2",), pgo=True),
            fb.FlagSet("O3 fast-math", ("-O3", "-ffast-math", "-mavx2"))]
    rows = fb.run_matrix([src], sets, repeats=1, out_dir=tmp_path / "bin")
    ok = {r["name"]: r["ok"] for r in rows}
    assert ok["O2"] and ok["O0"] and ok["O2 PGO"]
    assert not ok["O3 fast-math"]           # the vectorised, reassociated float sum differs
    assert all(r["ns"] > 0 for r in rows)
