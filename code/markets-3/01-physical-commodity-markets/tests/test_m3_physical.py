"""Tests of the Chapter 1 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_physical import back_to_back, hedged_sd_theory, load_differential, simulate_cargo


def test_hedge_leaves_only_basis_over_many_seeds():
    for seed in range(5):
        s = simulate_cargo(n_paths=20_000, seed=seed)
        assert abs(s["hedged"].std() - hedged_sd_theory()) < 0.02
        assert abs(s["hedged"].mean() - 80.10) < 0.02            # F0 + B0 + DIFF


def test_back_to_back_is_flat_outside_the_periods():
    bb = back_to_back()
    prof = dict(bb["profile"])
    assert prof[0] == 0 and prof[33] == 0 and prof[20] == 700_000


def test_differential_file():
    rows = load_differential()
    assert len(rows) == 320 and rows[0][0] == "2000-01" and rows[-1][0] == "2026-08"
