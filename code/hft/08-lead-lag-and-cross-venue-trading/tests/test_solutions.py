"""Numbers gate: every numerical answer printed in Book 11, chapter 8 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_leadlag as h  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


def test_leads_and_shares():
    t = h.table()
    assert [[r(x) for x in t[lag]["lead"]] for lag in h.LAGS] == [[0.05, 0.25], [0.225, 0.25], [0.475, 0.575],
                                                                  [1.075, 1.1]]
    assert [(r(t[g]["is_low"], 2), r(t[g]["is_high"], 2), r(t[g]["component"], 2)) for g in h.LAGS] == [
        (0.52, 0.73, 0.57), (0.81, 0.9, 0.73), (0.97, 0.98, 0.87), (1.0, 1.0, 0.98)]
    assert r(t[1.0]["is_low"]) == 0.998 and r(t[1.0]["is_high"]) == 0.998


def test_edge_curve():
    c = h.edge_curve()
    assert [r(c[x]["edge"], 3) for x in (0.001, 0.05)] == [0.485, 0.463]
    assert [r(c[x]["edge"], 2) for x in (0.1, 0.3, 0.5, 1.0)] == [0.43, 0.24, -0.22, -0.54]
    assert c[0.001]["trades"] == 135 and r(c[0.2]["edge"]) == 0.363
    assert (r(h.edge(0.2, 0.001)["edge"]), r(h.edge(0.2, 0.1)["edge"])) == (0.444, 0.142)


def test_exercises():
    assert r(0.18 / (0.18 + 0.02), 1) == 0.9 and round(67.5 * 0.363 * 100 * 0.01, 2) == 24.5 and round(97 / 7) == 14
