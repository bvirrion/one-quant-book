# ruff: noqa: B019, UP033
import gc
import weakref
from functools import lru_cache


class Pricer:
    def __init__(self, curve):
        self.curve = curve

    @lru_cache(maxsize=None)
    def price(self, strike):
        return self.curve[0] * strike


p = Pricer([1.5] * 1_000_000)
print(p.price(100))
ref = weakref.ref(p)
del p
gc.collect()
print(ref() is None)
