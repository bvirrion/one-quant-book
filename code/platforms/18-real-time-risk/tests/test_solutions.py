"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 18 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_rtrisk as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/18-real-time-risk"


def test_small_runs():
    r = P.afternoon(seed=5)
    s = r["series"]
    assert abs(s[:, 3]).max() <= P.LIMIT and abs(s[:, 4]).max() <= P.LIMIT and len(r["fills"]["desk B"]) > 0


def test_named_result_numbers():
    r = P.afternoon()
    t = r["firm_alert"][0]
    assert (int(t // 3600), int(t % 3600 // 60), int(t % 60)) == (14, 23, 50)
    assert [a[1] for a in r["alerts"]] == ["firm"]
    s = r["series"]
    assert round(abs(s[:, 3]).max() / 1e6, 1) == 49.3 and round(abs(s[:, 4]).max() / 1e6, 1) == 43.6
    assert (round(s[-1][2] / 1e6, 1), round(s[-1][3] / 1e6, 1), round(s[-1][4] / 1e6, 1)) == (-90.8, -47.6, -43.2)
    assert round(abs(s[-1][2]) / P.LIMIT, 2) == 1.82 and round(abs(s[:, 2]).max() / 1e6, 1) == 92.4
    assert (r["refreshes"], round(r["close_spot"], 1), len(r["fills"]["desk A"]), len(r["fills"]["desk B"])) \
        == (6, 4908.5, 21, 22)
    assert sum(q for _i, q in P.book_at_close(r)) == 21_000
    w = P.what_if_at_close(r)
    assert w["breached"] == ["firm"] and round(w["after"]["firm"] / 1e6, 1) == -92.8
    assert round(r["agg"].snapshot(17.5 * 3600).cache_age) == 3890
    rows = P.approximation_error(r)
    assert P.one_percent_move(rows) == 0.035
    neg = [x for x, _a, _f, e in rows if e > 0.01 and x < 0]
    assert round(max(neg), 4) == -0.0675
    at = {round(x, 4): e for x, _a, _f, e in rows}
    assert at[0.01] < 1e-6 and at[-0.01] < 1e-6 and round(100 * at[0.1], 1) == 23.6 and round(100 * at[-0.1], 1) == 3.9


def test_chart_data():
    rows = list(csv.DictReader(open(FIG / "approximation.csv")))
    assert len(rows) == 81 and rows[0]["move_pct"] == "-10.00"


def test_exercise_7_thresholds():
    got = []
    for th in (0.001, 0.02):
        r = P.afternoon(threshold=th)
        got.append((r["refreshes"], round(r["series"][-1][2] / 1e6, 3), r["firm_alert"][0]))
    assert got == [(105, -90.837, 51830.0), (1, -90.832, 51830.0)]
    assert int(0.9 * 50e6 // (0.4 * 1000 * 5000)) == 22
