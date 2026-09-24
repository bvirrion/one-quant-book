import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "cdscurve"))
import firm_structural as f
from firm_cdscurve import HazardCurve, par_spread


def test_inversion_round_trips_equity_and_its_volatility():
    V, s = f.invert(10.0, 0.5, 40.0, 5.0, 0.04)
    assert abs(f.merton_equity(V, 40.0, 5.0, 0.04, s) - 10.0) < 1e-9
    assert abs(f.equity_vol(V, 40.0, 5.0, 0.04, s) - 0.5) < 1e-9
    assert abs(f.asset_from_equity(10.0, s, 40.0, 5.0, 0.04) - V) < 1e-9


def test_debt_is_assets_minus_equity_and_below_riskless():
    V, D, T, r, s = 50.0, 40.0, 5.0, 0.04, 0.2
    debt = f.merton_debt(V, D, T, r, s)
    assert debt < D * math.exp(-r * T) and abs(debt + f.merton_equity(V, D, T, r, s) - V) < 1e-12
    assert f.merton_spread(500.0, D, T, r, 0.05) < 1e-12


def test_first_passage_matches_reflection_without_drift():
    x, s, t = math.log(1.5), 0.3, 2.0
    q = f.first_passage_survival(1.5, 1.0, t, 0.5 * s * s, s)
    assert abs(q - (2 * f.ncdf(x / (s * math.sqrt(t))) - 1)) < 1e-12
    assert f.first_passage_survival(1.0, 1e-12, 5.0, 0.04, 0.3) > 1 - 1e-12


def test_barrier_survival_is_below_terminal_survival():
    V, B, r, s = 40.0, 30.0, 0.04, 0.2
    for t in (1.0, 5.0):
        assert f.first_passage_survival(V, B, t, r, s) < 1 - f.merton_pd(V, B, t, r, s)


def test_model_cds_spread_of_a_flat_hazard_is_the_cdscurve_par_spread():
    lam, r = 0.02, 0.03
    s = f.model_cds_spread(lambda t: math.exp(-lam * t), r, 5.0, 0.4)
    assert abs(s - par_spread(HazardCurve([5.0], [lam]), f.FlatDisc(r), 5.0, 0.4)) < 1e-12
