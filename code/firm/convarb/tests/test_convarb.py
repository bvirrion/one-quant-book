import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "convertible"))
from firm_convarb import ArbConfig, delta, mark, run_book, scenario, value_tables  # noqa: E402
from firm_convertible import value_at  # noqa: E402

CFG = ArbConfig(maturity=1.0, stress_start=100, stress_len=20, recovery_days=40, new_issue_days=50)


def test_scenario_shape():
    s = scenario(252, CFG)
    assert abs(s["cheap"][0] - 0.03) < 1e-12 and abs(s["cheap"][60] - 0.01) < 1e-12
    assert s["stressed"][100:120].all() and not s["stressed"][99] and abs(s["cheap"][119] - 0.06) < 1e-12
    assert abs(s["cheap"][170] - 0.01) < 1e-12 and s["fee"][110] == 0.05


def test_marks_match_the_table_and_delta_is_sensible():
    tables = value_tables(CFG)
    taus, spots, normal, stressed = tables
    assert abs(mark(tables, taus[0], 40.0) - value_at(40.0, (spots, normal[0]))) < 1e-9
    assert mark(tables, 1.0, 40.0, True) < mark(tables, 1.0, 40.0, False)          # more hazard, lower value
    assert 0 < delta(tables, 1.0, 40.0) < 2.5                                        # below the conversion ratio


def test_buckets_add_up_on_a_calm_path():
    cfg = ArbConfig(maturity=1.0, stress_start=10_000)
    S = np.exp(np.linspace(0, 0.05, 240))
    b = run_book(S, cfg)
    parts = sum(b[k] for k in ("bond", "hedge", "cheapness", "credit", "credit_hedge", "coupon", "borrow"))
    assert np.allclose(parts, b["total"]) and np.allclose(b["credit"], 0)
