import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from index_recon import event_path, passive_demand, ranks, reconstitute, simulate_turnover


def test_ranks_and_plain_top_n():
    caps = np.array([5.0, 9.0, 1.0, 7.0])
    assert list(ranks(caps)) == [3, 1, 4, 2]
    new = reconstitute(caps, np.array([False] * 4), 2, 0)
    assert list(new) == [False, True, False, True]


def test_buffer_keeps_a_member_and_blocks_an_outsider():
    caps = np.array([10.0, 9.0, 8.0, 7.0, 6.0, 5.0])
    member = np.array([True, True, False, False, True, False])      # rank 5 is a member, rank 3 is not
    assert list(reconstitute(caps, member, 3, 0)) == [True, True, True, False, False, False]
    assert list(reconstitute(caps, member, 3, 2)) == [True, True, False, False, True, False]
    assert reconstitute(caps, member, 3, 1).sum() == 3


def test_always_exactly_n_members_and_buffers_cut_turnover():
    none = simulate_turnover(600, 200, 0, 20, 3)
    wide = simulate_turnover(600, 200, 30, 20, 3)
    assert wide[0] < none[0] and wide[1] < none[1]


def test_demand_and_event_path():
    assert passive_demand(1000.0, 50_000.0, 100.0) == pytest.approx(2.0)
    car = event_path(10, 20, -5, 0.01, 0.04, 5.0)
    assert car[0] == 0.0 and car[10] == pytest.approx(0.05) and car[15] == pytest.approx(0.03)
    assert car[-1] < 0.013
