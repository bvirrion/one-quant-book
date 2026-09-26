"""Acceptance tests for firm.mlmonitor (Book 12, chapter 27)."""
import pathlib
import sys

import numpy as np
from scipy.stats import ks_2samp, spearmanr

_FIRM = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_FIRM / "mlmonitor"))
sys.path.insert(0, str(_FIRM / "exptrack"))
import firm_mlmonitor as mm  # noqa: E402
from firm_exptrack import AuditTrail, Registry  # noqa: E402


def test_psi_zero_on_itself_and_grows_with_shift():
    r = np.random.default_rng(0)
    ref = r.standard_normal(5000)
    assert mm.psi(ref, ref) < 1e-12
    vals = [mm.psi(ref, r.standard_normal(5000) + s) for s in (0.0, 0.2, 0.5)]
    assert vals[0] < 0.01 < vals[1] < vals[2]
    assert abs(mm.psi(mm.Reference(ref), ref + 0.3) - mm.psi(ref, ref + 0.3)) < 1e-12


def test_ks_and_ic_match_scipy_with_ties():
    r = np.random.default_rng(1)
    for k in range(50):
        a = np.round(r.standard_normal(r.integers(5, 300)), 1 if k % 2 else 6)
        b = np.round(r.standard_normal(r.integers(5, 200)) * 1.3 + 0.2, 1 if k % 2 else 6)
        assert abs(mm.ks(a, b) - ks_2samp(a, b).statistic) < 1e-12
    x, y = r.standard_normal(200), r.standard_normal(200)
    assert abs(mm.daily_ic(x, x + y) - spearmanr(x, x + y)[0]) < 1e-12


def test_cusum_alarms_on_a_drop_and_resets():
    c = mm.Cusum(target=0.1, k=0.02, h=0.1)
    assert not any(c.update(0.1) for _ in range(50))
    hits = [c.update(0.0) for _ in range(6)]
    assert hits == [False, True, False, True, False, True] and c.s == 0.0


def test_calibration_rates():
    r = np.random.default_rng(2)
    z = r.standard_normal((20, 400))
    th = mm.calibrate_daily(z.ravel(), 1 / 21)
    assert abs((z > th).mean() - 1 / 21) < 0.002
    tp = mm.calibrate_pages(z, 1 / 21)
    assert mm.onsets(z > tp).mean() <= 1 / 21 and tp <= th
    sticky = np.cumsum(r.standard_normal((20, 400)), axis=1) / 10       # a persistent statistic pages in spells
    assert mm.calibrate_pages(sticky, 1 / 21) < mm.calibrate_daily(sticky.ravel(), 1 / 21)
    assert mm.onsets(np.array([0, 1, 1, 0, 1], bool)).tolist() == [False, True, False, False, True]
    assert mm.first_alarm([0, 5, 0, 5], 1, 2) == 1 and mm.first_alarm([0, 0], 1, 0) is None


def test_shadow_verdict():
    r = np.random.default_rng(3)
    good, base = 0.10 + 0.07 * r.standard_normal(60), 0.0 + 0.07 * r.standard_normal(60)
    p = mm.shadow_verdict(good, base)
    assert (p[:9] == 1).all() and p[-1] < 0.001 and (np.diff(p) <= 0).all()
    false = 0
    for s in range(200):
        g = np.random.default_rng(100 + s)
        false += mm.shadow_verdict(0.07 * g.standard_normal(60), 0.07 * g.standard_normal(60)).min() < 0.05
    assert false / 200 <= 0.05


def test_rollback_restores_the_previous_version(tmp_path):
    reg = Registry(tmp_path, AuditTrail(tmp_path / "audit.jsonl"))
    rec = {"artefact": "a", "data": "d", "code": "c"}
    assert mm.rollback(reg, "m", "2026-01-01", "nothing") is None
    for v, ts in ((1, "2026-01-01"), (2, "2026-02-01"), (3, "2026-03-01")):
        reg.register("m", f"r{v}", rec, ts)
        reg.promote("m", v, "production", ts, "champion")
    assert mm.rollback(reg, "m", "2026-03-05", "IC alarm") == 2
    assert reg.current("m")["version"] == 2 and reg.as_of("m", "2026-03-02")["version"] == 3
    assert reg.audit.verify() == -1
