"""firm.locations -- what a package leaves after tax and housing, city by city (build of One Quant Book 17, ch. 27).

A city record ties a tax jurisdiction of firm.aftertax to an official rent statistic (with its measure, period and
source id, because rent statistics differ: an average, a median, a percentile, gross or net of charges) and to the
visa facts a candidate needs (ledger ids). Disposable pay after housing is the net pay of firm.aftertax minus twelve
months of the city's rent, in US dollars at the tax data's exchange rates. Two cities are compared by the package in
one that leaves the same disposable pay as a package in the other, and by the package at which they cross.

API (stable):
    City(name, location, rent_month, currency, measure, period, source, visas=())
    rent_usd_year(params, city) ; disposable(params, city, gross_usd, expat=False) -> dict(net, rent, disposable)
    equivalent(params, city_a, gross_a, city_b, lo, hi) -> gross in city_b with the same disposable pay
    crossing(params, city_a, city_b, lo, hi) -> gross at which the two cities' disposable pay are equal (or None)
"""
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "aftertax"))
import firm_aftertax as at  # noqa: E402


@dataclass(frozen=True)
class City:
    name: str
    location: str          # a firm.aftertax location key
    rent_month: float      # local currency a month
    currency: str
    measure: str           # e.g. 'average, two bedrooms', 'median net rent, three rooms'
    period: str
    source: str            # ledger id
    visas: tuple = ()


def rent_usd_year(params, city):
    return 12.0 * city.rent_month / at.local_per_usd(params, city.location)


def disposable(params, city, gross_usd, expat=False):
    net = at.net_usd(params, city.location, gross_usd, expat)["net"]
    rent = rent_usd_year(params, city)
    return {"net": net, "rent": rent, "disposable": net - rent}


def _solve(f, lo, hi, tol=1.0):
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (fhi > 0):
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def equivalent(params, city_a, gross_a, city_b, lo=1e4, hi=1e8):
    target = disposable(params, city_a, gross_a)["disposable"]
    return _solve(lambda g: disposable(params, city_b, g)["disposable"] - target, lo, hi)


def crossing(params, city_a, city_b, lo=5e4, hi=5e6):
    return _solve(lambda g: disposable(params, city_a, g)["disposable"] - disposable(params, city_b, g)["disposable"],
                  lo, hi)
