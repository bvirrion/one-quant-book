import pathlib
import sys
from dataclasses import replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from withdrawal import Params, depth_needed, run, trough


def test_feedback_turns_a_large_order_into_a_crash_and_a_pause_limits_it():
    base = Params()
    fb = trough(run(base, 75_000))
    none = trough(run(replace(base, withdrawal=0.0, churn=0.0), 75_000))
    paused = trough(run(replace(base, pause_at=0.05), 75_000))
    assert none < 0.03 < 0.05 < paused < fb


def test_each_feedback_alone_is_mild_and_a_slow_programme_is_safe():
    base = Params()
    none = trough(run(replace(base, withdrawal=0.0, churn=0.0), 75_000))
    only_churn = trough(run(replace(base, withdrawal=0.0), 75_000))
    only_withdrawal = trough(run(replace(base, churn=0.0), 75_000))
    slow = trough(run(replace(base, participation=0.03), 75_000, minutes=200))
    assert abs(only_churn - none) < 1e-3 and only_withdrawal < 0.045 and slow < 0.03 < 0.09 < trough(run(base, 75_000))


def test_the_result_does_not_depend_on_the_time_step():
    assert abs(trough(run(Params(), 75_000, sub=60)) - trough(run(Params(), 75_000, sub=240))) < 0.003


def test_everything_is_sold_in_every_case():
    for p in (Params(), Params(withdrawal=0.0, churn=0.0), Params(pause_at=0.05)):
        assert abs(sum(x[2] for x in run(p, 75_000)) - 75_000) < 1e-6


def test_depth_needed_is_monotone_in_the_tolerated_fall():
    a, b = depth_needed(Params(), 75_000, 0.02), depth_needed(Params(), 75_000, 0.03)
    assert a > b > 0 and trough(run(replace(Params(), depth0=a * 1.01), 75_000)) <= 0.02
