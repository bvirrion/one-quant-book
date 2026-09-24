"""Tutorial of Book 6, chapter 11: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_inflation as m


def test_convexity_grows_and_simulation_agrees():
    adj = [r[3] for r in m.convexity_table()]
    assert adj[0] == 0.0 and all(b < a for a, b in zip(adj[1:], adj[2:], strict=False))
    exact, mc, se = m.mc_check()
    assert abs(mc - exact) < 3 * se


def test_seasonal_path_meets_annual_points():
    p = m.seasonal_forward_path()
    assert abs(p[12][1] - p[12][2]) < 1e-9 and abs(p[24][1] - p[24][2]) < 1e-9
