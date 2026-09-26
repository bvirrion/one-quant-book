import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "coreplan"))
import firm_coreplan as cp  # noqa: E402
import firm_perfgate as pg  # noqa: E402


def test_interleave():
    assert pg.interleave(3) == ["A", "B", "B", "A", "A", "B"]


def test_compare_flags_a_clear_rise_and_not_noise():
    rng = random.Random(0)
    a = [100 + rng.gauss(0, 5) for _ in range(40)]
    same = [100 + rng.gauss(0, 5) for _ in range(40)]
    worse = [110 + rng.gauss(0, 5) for _ in range(40)]
    v = pg.compare(a, worse)
    assert v.regression and 0.07 < v.rise < 0.13 and v.low < v.rise < v.high and v.p_value < 0.01
    assert not pg.compare(a, same).regression
    small = [x * 1.01 for x in a]                                 # real (every run 1% slower) but under the tolerance
    v = pg.compare(a, small)
    assert abs(v.rise - 0.01) < 1e-9 and not v.regression


def test_power_and_false_alarms_on_synthetic_noise():
    rng = random.Random(1)
    pool = [100 * rng.lognormvariate(0, 0.15) for _ in range(400)]
    a, b = pool[:200], pool[200:]
    assert pg.power(a, b, 20, trials=100) <= 0.10                 # false alarms near alpha, under the tolerance rule
    assert pg.power(a, b, 20, trials=100, shift=5.0) < pg.power(a, b, 80, trials=100, shift=5.0)
    assert pg.power(a, b, 80, trials=100, shift=15.0) > 0.9
    assert 150 < pg.runs_needed(0.15, 0.05) < 260 and pg.runs_needed(0.15, 0.10) < pg.runs_needed(0.15, 0.05)


def test_certification_script_passes_and_catches_a_wrong_venue_behaviour():
    script = pg.load_script(HERE / "data/cert_script.json")
    res = pg.certify(script)
    assert len(res) == 17 and all(ok for _, ok, _ in res)
    wrong = [dict(s) for s in script]
    wrong[3]["expect"] = [["C", "U"]]                              # expects a second cancel to succeed
    assert [ok for _, ok, _ in pg.certify(wrong)].count(False) == 1


def test_preflight_uses_the_tuning_audit():
    ta = HERE.parent / "tuneaudit/data"
    plan = cp.plan(cp.read_topology(HERE.parent / "coreplan/data/two_socket"), "ens1f0")
    ok, findings = pg.preflight(ta / "tuned", plan)
    assert ok and findings
    ok, findings = pg.preflight(ta / "mistuned", plan)
    assert not ok and any(f.status == "fail" for f in findings)
