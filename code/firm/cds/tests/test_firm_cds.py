"""Acceptance tests of the Book 2, Chapter 23 build (CDS pricing and the auction)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_cds import (
    Cds,
    cash_settlement,
    final_price,
    hazard_from_spread,
    inside_market_midpoint,
    open_interest,
    par_spread,
    upfront,
    upfront_from_spread,
)

# Lehman Brothers, 10 October 2008 (Helwege, Maurer, Sarkar and Wang, FRBNY Staff Report 372, Box 1)
BIDS = [8, 8, 8, 8, 8.25, 8.75, 8.875, 9, 9, 9.25, 9.25, 9.5, 9.5, 10]
OFFERS = [10, 10, 10, 10, 10.25, 10.75, 10.875, 11, 11, 11, 11.25, 11.5, 11.5, 12]
REQUESTS = [("buy", 130), ("sell", 755), ("sell", 870), ("sell", 141), ("sell", 480), ("sell", 464), ("sell", 1470),
            ("sell", 390), ("buy", 612), ("sell", 574), ("sell", 191), ("sell", 170), ("buy", 30), ("sell", 187)]


def test_credit_triangle_and_par():
    cds = Cds(5.0, 0.01)
    lam = hazard_from_spread(cds, 0.01, 0.04)
    assert math.isclose(par_spread(cds, lam, 0.04), 0.01, rel_tol=1e-9)
    assert abs(lam - 0.01 / 0.6) < 0.0005                     # spread ~ lam (1 - R)
    assert abs(upfront(cds, lam, 0.04)) < 1e-12               # at the par spread, no upfront


def test_upfront_signs():
    cds = Cds(5.0, 0.05)
    assert upfront_from_spread(cds, 0.03, 0.04) < 0 < upfront_from_spread(cds, 0.08, 0.04)


def test_lehman_first_stage():
    assert inside_market_midpoint(BIDS, OFFERS) == 9.75
    assert open_interest(REQUESTS) == 4920


def test_second_stage_and_settlement():
    orders = [(11.0, 100), (10.0, 400), (9.0, 1500), (8.625, 3000), (7.0, 5000)]
    assert final_price(9.75, 4920, orders) == 8.625
    assert final_price(9.75, 4920, [(12.0, 6000)]) == 10.75      # capped one point above the midpoint
    assert final_price(9.75, 0, orders) == 9.75
    assert cash_settlement(10e6, 8.625) == 9_137_500
