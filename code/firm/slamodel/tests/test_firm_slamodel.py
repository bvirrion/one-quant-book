import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_slamodel as sm  # noqa: E402

C = sm.Circuit("c", "10 Gb", 1000.0, 0.0, 4383.0, 4.0, "x", "2026-09-28")


def test_availability_by_hand():
    assert sm.availability(99, 1) == 0.99
    single = sm.Design("s", (C,))
    diverse = sm.Design("d", (C, C))
    duct = sm.Design("u", (C, C), 0.5, 12.0)
    u = 1 - sm.availability(4383, 4)
    assert sm.design_availability(single) == pytest.approx(1 - u)
    assert sm.design_availability(diverse) == pytest.approx(1 - u * u)
    assert 1 - sm.design_availability(duct) == pytest.approx(u * u + 6 / sm.HOURS_Y - u * u * 6 / sm.HOURS_Y)
    assert sm.expected_down_min(single) == pytest.approx(u * sm.HOURS_Y * 60)


def test_simulation_agrees_with_steady_state():
    single = sm.Design("s", (C,))
    sims = [sm.simulate_year(single, seed=k)["down_min"] for k in range(1500)]
    assert np.mean(sims) == pytest.approx(sm.expected_down_min(single), rel=0.08)
    y = sm.simulate_year(sm.Design("u", (C, C), 0.5, 12.0), seed=3)
    assert y["down_min"] == pytest.approx(sum(sm.monthly_down_min(y["intervals"])))
    assert y["down_min"] <= min(y["per_circuit_down_min"]) + 1e-9


def test_credits():
    t = sm.SCHEDULES["single connection"]
    assert sm.credit(t, 99.0, 1000) == 0 and sm.credit(t, 94.0, 1000) == 100 and sm.credit(t, 91.0, 1000) == 250
    assert sm.credit(t, 80.0, 1000) == 1000
    assert sm.credit(sm.SCHEDULES["multi-site redundant"], 99.95, 1000) == 100
    assert sm.uptime_pct(432, 30) == pytest.approx(99.0)
    assert sm.downtime_cost(10, 2000) == 20000 and sm.nines(0.999) == pytest.approx(3)
