"""How much to buy from a constant-product pool to sell at an outside price, after its fee."""
import math


def best_input(x, y, outside, fee=0.003):
    """Dollars to spend on a pool of x tokens and y dollars, to resell at `outside`."""
    keep = 1 - fee
    return max(0.0, (math.sqrt(keep * x * y * outside) - y) / keep)


def profit(dollars, x, y, outside, fee=0.003, gas=0.0):
    keep = 1 - fee
    tokens = dollars * keep * x / (y + dollars * keep)
    return tokens * outside - dollars - gas
