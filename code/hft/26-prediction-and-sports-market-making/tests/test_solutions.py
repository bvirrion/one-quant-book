"""Numbers gate: every numerical answer printed in Book 11, chapter 26 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_sports as h  # noqa: E402

sm = h.sm


def r(x, d=0):
    return round(float(x), d)


def test_model_and_quote():
    assert (r(sm.home_win(1.5, 1.1, 1.0, 0), 3), r(sm.home_win(1.5, 1.1, 0.5, 1), 3)) == (0.464, 0.76)
    b, n, o = sm.odds_quote(0.46, 0.01)
    assert (r(b, 2), r(n, 2), r(o, 2)) == (2.13, 1.82, 0.02)
    assert r(sm.home_win(1.3, 1.3, 10 / 90, 1), 2) == 0.88


def test_delay():
    b = h.by_delay()
    assert [r(b[d]["loss_per_goal"]) for d in (0.0, 2.0, 3.0, 4.0, 6.0)] == [236, 168, 66, 20, 1]
    assert [r(100 * b[d]["sniped_share"]) for d in (0.0, 2.0, 3.0, 4.0)] == [100, 72, 29, 8]
    assert r(b[0.0]["net_per_match"]) == -528 and b[0.0]["spread_per_match"] == 90.0 and b[4.0]["net_per_match"] > 0
    assert h.negligible() == 6.0 and r(b[0.0]["goals_per_match"] * h.N) == 5241


def test_caps_and_feed():
    c = h.caps()
    assert (r(c[100.0]["loss_per_goal"]), r(c[50.0]["loss_per_goal"])) == (24, 12)
    f = h.faster_feed()
    assert f["negligible"] == 3.0 and (r(f["rows"][1.0]), r(f["rows"][2.0]), r(f["rows"][3.0], 1)) == (112, 10, 0.6)
