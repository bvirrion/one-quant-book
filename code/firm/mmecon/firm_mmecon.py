"""firm.mmecon -- the unit economics of a market maker (One Quant Book 11, chapter 1).

A market maker's income is a capture per unit traded times the volume it trades; its costs split into those that
scale with volume (exchange and clearing fees, payment for order flow, financing of the inventory) and those that do
not (people, machines, data, connectivity, memberships). The fixed part makes the business one of scale: below a
break-even volume every day loses money, above it profit grows faster than volume (operating leverage). All amounts
are in one currency per day unless stated; capture and variable cost are per unit of value traded (for example basis
points) or per share, the same unit as the volume.

API (stable):
    capture(income, volume)                          income per unit of volume
    capture_bp(income, value_traded)                 income per unit of value traded, in basis points
    profit(volume, capture, variable, fixed)         (capture - variable) * volume - fixed
    breakeven_volume(capture, variable, fixed)       fixed / (capture - variable); inf if the margin is not positive
    operating_leverage(volume, capture, variable, fixed)
                                                     d ln(profit) / d ln(volume) = margin * volume / profit
    per_day(total, days)                             a period total as a daily average
    cost_shares(costs)                               {line: share of the total} for a dict of cost lines
    profit_curve(volumes, capture, variable, fixed)  profit at each volume (numpy array)
"""
from __future__ import annotations

import math

import numpy as np


def capture(income: float, volume: float) -> float:
    return income / volume


def capture_bp(income: float, value_traded: float) -> float:
    return 1e4 * income / value_traded


def profit(volume, capture: float, variable: float, fixed: float):
    return (capture - variable) * np.asarray(volume, float) - fixed


def breakeven_volume(capture: float, variable: float, fixed: float) -> float:
    margin = capture - variable
    return fixed / margin if margin > 0 else math.inf


def operating_leverage(volume: float, capture: float, variable: float, fixed: float) -> float:
    p = float(profit(volume, capture, variable, fixed))
    if p <= 0:
        raise ValueError("operating leverage is defined above break-even only")
    return (capture - variable) * volume / p


def per_day(total: float, days: float) -> float:
    return total / days


def cost_shares(costs: dict) -> dict:
    total = sum(costs.values())
    return {k: v / total for k, v in costs.items()}


def profit_curve(volumes, capture: float, variable: float, fixed: float) -> np.ndarray:
    return profit(volumes, capture, variable, fixed)
