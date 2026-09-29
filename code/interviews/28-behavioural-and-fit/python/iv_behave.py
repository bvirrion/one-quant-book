"""Book 18, chapter 28: the one piece of arithmetic in the loss question: how often a k-standard-deviation
loss day occurs under a normal and under a fat-tailed (unit-variance Student t) model."""
from math import sqrt

from scipy.stats import norm, t


def days_between(k_sd: float, dist: str = "normal", dof: int = 3) -> float:
    if dist == "normal":
        p = norm.cdf(-k_sd)
    else:
        p = t.cdf(-k_sd * sqrt(dof / (dof - 2)), dof)  # unit-variance t: scale sqrt((dof - 2) / dof)
    return 1 / p
