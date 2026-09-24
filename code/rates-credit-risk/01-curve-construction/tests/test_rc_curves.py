"""Tutorial of Book 6, chapter 1: the printed end state is reproduced."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_curves as m


def test_four_calibrations_converge():
    for cal in m.curves().values():
        assert cal.iterations == 3 and cal.max_error < 1e-12


def test_svensson_reproduces_the_ecb_published_rates():
    for t, z in m.ECB_SPOT_2026_09_22.items():
        assert m.svensson(t, **m.ECB_2026_09_22) == pytest.approx(z, abs=1e-6)


def test_eight_year_buckets_sum_to_the_parallel_dv01():
    b = m.off_pillar_buckets(8)
    sums = {k: sum(v) for k, v in b.items()}
    assert all(abs(s - 69_600) < 50 for s in sums.values())


def test_locality_flat_forward_moves_only_five_to_ten_years():
    for t, _lz, ff, _cs, _mc in m.locality("7Y", step=0.5):
        if t <= 5.0 or t > 10.5:
            assert abs(ff) < 0.05
    far = [abs(r[3]) for r in m.locality("7Y", step=0.5) if 12 < r[0] < 15]
    assert max(far) > 0.2
