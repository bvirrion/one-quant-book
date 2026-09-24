"""Acceptance tests of the Book 2, Chapter 15 build (last-look simulation and TCA)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_lastlook import check, expected_transfer, simulate, tca


def test_policies():
    assert check(5, 0, "none") and check(-5, 0, "asymmetric") and not check(0.2, 0.1, "asymmetric")
    assert not check(-0.2, 0.1, "symmetric") and check(0.05, 0.1, "symmetric")


def test_no_last_look_fills_everything():
    t = tca(simulate(2000, 0.01, 100, 0.0, "none"), 0.5)
    assert t["fill_ratio"] == 1.0


def test_asymmetric_transfer_matches_closed_form():
    sims = simulate(200_000, 0.01, 100, 0.0, "asymmetric", seed=7)
    kept = sum(r.move_at_decision for r in sims if not r.accepted) / len(sims)
    assert math.isclose(kept, expected_transfer(0.01, 100, 0.0, "asymmetric"), rel_tol=0.02)
    assert expected_transfer(0.01, 100, 0.05, "symmetric") == 0.0


def test_informed_clients_are_rejected_more():
    t = tca(simulate(50_000, 0.01, 100, 0.05, "asymmetric", informed_share=0.2, edge=0.2, seed=3), 0.5)
    assert t["reject_informed"] > 0.9 > 0.4 > t["reject_uninformed"]
