# ruff: noqa: B019, UP033
from functools import lru_cache


class Pricer:
    def __init__(self, n):
        self.curve = [0.01] * n

    @lru_cache(maxsize=None)
    def price(self, strike):
        return strike * self.curve[0]


def one_request(n=10_000):
    return Pricer(n).price(100)
