"""Numbers gate: every numerical answer printed in Book 16, chapter 25 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_launch as m  # noqa: E402

fl = m.fl


def r(x, d=1):
    return round(float(x), d)


def test_closed_forms():
    assert (fl.years_for_t(1.0), r(fl.years_for_t(1.5), 2), r(fl.tstat(1.5, 2), 2)) == (4.0, 1.78, 2.12)
    assert r(fl.breakeven_aum(m.BASE, 0.10)) == 87.6 and r(fl.breakeven_aum(fl.Launch(revenue_share=0.0), 0.10)) == 69.8
    terms = fl.ff.FeeTerms(mgmt=0.015, perf=0.20)
    assert r(fl.annual_fees(1.0, 0.10, terms) * 100, 2) == 3.2
    assert r(2.2 / (0.032 * 0.8 - 0.0005)) == 87.6


def test_simulation():
    s = m.summary()
    a, b = s["seeded, 20% revenue share"], s["unseeded, $15 million"]
    assert (r(100 * a["p36"]), a["median_month"], [r(x) for x in a["q36"]]) == (43.2, 32.0, [30.7, 88.9, 186.0])
    assert (r(a["manager"], 2), r(a["seeder"], 2), r(100 * a["below_be_60"])) == (7.52, 4.21, 32.3)
    assert (r(100 * b["p36"], 2), b["median_month"], r(b["manager"], 2), r(100 * b["below_be_60"])) == (0.25, 51.0, -2.85, 64.5)
    assert r(a["manager"] - b["manager"], 2) == 10.37


def test_small_runs():
    a, f = fl.simulate(m.BASE, 1, 50, 12)
    assert a.shape == (50, 12) and (a >= 0).all() and (f >= 0).all()


def test_exercises():
    from dataclasses import replace
    launch = replace(m.BASE, revenue_share=0.10)
    a, f = fl.simulate(launch, 25, 2000, 60)
    assert (r(fl.breakeven_aum(launch, 0.10)), r(fl.manager_value(a, f, launch), 2), r(fl.seed_value(f, 0.10), 2)) == (
        77.7, 9.62, 2.1)
    assert fl.years_for_t(0.5) == 16.0 and r(2 / 0.02) == 100.0 and r(2 / (0.02 * 0.75), 1) == 133.3
    assert r(1 / 5 ** 0.5, 2) == 0.45
