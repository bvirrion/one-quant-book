"""Numbers gate: every numerical answer printed in Book 12, chapter 28 (text and solutions)."""
import filecmp
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_team as m  # noqa: E402


def test_package_is_reproducible_and_passes(tmp_path):
    m.write_package(tmp_path)
    for f in ("manifest.json", "feature_vectors.csv"):
        assert filecmp.cmp(tmp_path / f, m.PACKAGE / f, shallow=False)
    pkg = m.load(m.PACKAGE / "manifest.json")
    assert len(pkg["features"]) == 16 and pkg["tolerance"] == 1e-12 and len(pkg["monitoring"]) == 4
    assert (pkg["latency_budget_us"], pkg["latency_measured_us"]) == (5.0, 2.6) and len(pkg["card"]) == 15
    assert len(np.loadtxt(pkg["test_vectors"], delimiter=",")) == 200
    assert len(m.checks_run()) == 9


def test_handoff_table():
    t = m.handoff_table()
    assert t == {"clean": [], "artefact rebuilt after hashing": ["artefact hash", "test vectors"],
                 "input the feed does not carry": ["feature specification"],
                 "window in milliseconds": ["feature vectors"], "one feature missing": ["feature specification"],
                 "another model's test vectors": ["test vectors"], "library latency": ["latency"],
                 "monitor without owner": ["monitoring"], "card without limitations": ["model card"]}


def test_pipeline_table():
    a, b = m.pipeline(True), m.pipeline(False, 1.0)
    assert m.RATE == 0.35 and m.N_MODELS - m.BURN == 3500 and round(52 * m.RATE) == 18
    assert tuple(round(a[k], 1) for k in ("median", "q25", "q75", "q90")) == (20.4, 14.8, 30.2, 42.9)
    assert tuple(round(b[k], 1) for k in ("median", "q25", "q75", "q90")) == (11.1, 9.6, 13.7, 16.5)
    assert (round(a["reach"], 3), round(b["reach"], 3)) == (0.351, 0.375)
    assert [round(v, 3) for v in a["lost"].values()] == [0.411, 0.053, 0.079, 0.087, 0.019]
    assert [round(v, 3) for v in b["lost"].values()] == [0.395, 0.035, 0.069, 0.103, 0.022]
    assert round(1 - a["reach"], 2) == 0.65
    assert (round(a["build visits"], 2), round(b["build visits"], 2)) == (1.79, 1.14)
    assert (round(a["build utilisation"], 2), round(b["build utilisation"], 2)) == (0.74, 0.12)
    assert round(a["median"] - b["median"], 1) == 9.3 and round((a["median"] - b["median"]) / a["median"], 2) == 0.45
    assert round(m.lead_by_stage(True)["no queues"], 1) == 14.9
    assert round(a["median"] / 52 * 12, 1) == 4.7                          # about five months


def test_checks_of_the_simulator():
    c = m.mm1_check()
    assert (round(c["W sim"], 2), c["W theory"] == 5.0 or round(c["W theory"], 6) == 5.0) == (5.05, True)
    assert (round(c["L chain"], 2), round(c["L little"], 2), round(c["p0 chain"], 2)) == (4.0, 4.04, 0.2)
    ll = m.littles_law()
    assert (round(ll["wip"], 2), round(ll["rate x time"], 2), round(ll["mean time"], 1)) == (4.87, 4.9, 14.0)


def test_rate_curve_and_third_engineer():
    rates, c = m.rate_curve()
    assert rates[0] == 0.2 and rates[3] == 0.35 and rates[-1] == 0.44
    assert (round(c[True][0]), round(c[True][3]), round(c[True][-1])) == (16, 22, 70)
    assert all(10.5 < v < 11.7 for v in c[False])
    med, util = m.third_engineer()
    assert (round(med, 1), round(util, 2)) == (16.6, 0.5)
    assert (round(c[True][3], 1), round(c[False][3], 1)) == (22.3, 11.1)


def test_mm1_arithmetic():
    assert round(0.74 / 0.26, 1) == 2.8 and round(0.9 / 0.1) == 9 and round(9 / (0.74 / 0.26), 1) == 3.2
    assert round(0.8 * 5.05, 2) == 4.04
