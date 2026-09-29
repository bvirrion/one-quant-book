import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_powerlink as pl  # noqa: E402


def test_race_symmetry_and_order():
    same = [pl.Participant(f"p{i}", 10.0) for i in range(4)]
    r = pl.capacity_race(same, n=8000)
    assert all(abs(v - 0.25) < 0.02 for v in r.values())
    fixed = [pl.Participant("fast", 1.0, 0.0), pl.Participant("slow", 5.0, 0.0), pl.Participant("slower", 9.0, 0.0)]
    assert pl.capacity_race(fixed, slots=2, n=10) == {"fast": 1.0, "slow": 1.0, "slower": 0.0}


def test_betfair_arithmetic():
    w = pl.load_weights()
    assert w["EX_BEST_OFFERS"] == 5 and w["EX_ALL_OFFERS+EX_TRADED"] == 32
    assert pl.markets_per_request(5) == 40 and pl.poll_requests_per_s(1000, 5, 5) == 125
    assert pl.poll_staleness_ms(5, 10.0) == 110.0
    assert pl.charged_transactions(7200) == 2200 and pl.charged_transactions(100) == 0
    assert pl.gate_closure(600) == 540
