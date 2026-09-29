"""firm.aftertax -- what a pay package is worth after tax, in eight places (build of One Quant Book 17, chapter 15).

Income tax and employee social contributions for a single employee without other income, as dated data: every
parameter is a row of data/industry/tax_2026.csv with a ledger id, and the Swiss federal tariff is the official table's
break points (ch_federal_tax_2026.csv). The functions below encode only the structure of each system: which base, which
brackets, which caps, which credits. They are deliberately simple: standard deductions only, no pension or charitable
deductions, no local taxes beyond the ones named, and New York's benefit recapture approximated by phasing each
bracket's flat rate in over the 50,000 of income above the bracket's start. The chapter says which simplification
matters where.

Locations (keys): london, new_york (federal + New York State + New York City), chicago (federal + Illinois),
amsterdam (optionally with the expat scheme), zurich (federal + canton + city, AHV/IV/EO and ALV), singapore,
hong_kong (the lower of progressive and standard rate, plus MPF), dubai (no income tax).

API (stable):
    load(path, fed_path) -> Params
    progressive(x, brackets) -> tax on x with [(upper, rate), ...]
    net_local(params, location, gross_local, expat=False) -> dict(tax, social, net)
    local_per_usd(params, location) -> units of local currency per US dollar
    net_usd(params, location, gross_usd, expat=False) -> dict(net, tax, social, avg_rate)
    marginal(params, location, gross_usd, step=1000.0, expat=False) -> marginal rate on the last `step` dollars
    LOCATIONS
"""
import bisect
import csv
import math
from dataclasses import dataclass, field

LOCATIONS = ("london", "new_york", "chicago", "amsterdam", "zurich", "singapore", "hong_kong", "dubai")
CURRENCY = {"london": "gbp", "new_york": "usd", "chicago": "usd", "amsterdam": "eur", "zurich": "chf",
            "singapore": "sgd", "hong_kong": "hkd", "dubai": "usd"}


def _parse(v):
    if ":" in v:
        out = []
        for part in v.split(";"):
            u, r = part.split(":")
            out.append((math.inf if u == "inf" else float(u), float(r)))
        return out
    return float(v)


@dataclass
class Params:
    p: dict
    fed_points: list = field(default_factory=list)

    def __getitem__(self, key):
        loc, name = key
        return self.p[loc][name]


def load(path, fed_path):
    p = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            p.setdefault(r["location"], {})[r["parameter"]] = _parse(r["value"])
    with open(fed_path) as f:
        pts = [(float(r["income"]), float(r["tax"])) for r in csv.DictReader(f)]
    return Params(p, pts)


def progressive(x, brackets):
    tax, lo = 0.0, 0.0
    for upper, rate in brackets:
        if x <= lo:
            break
        tax += (min(x, upper) - lo) * rate
        lo = upper
    return tax


def _rate_at(x, brackets):
    for upper, rate in brackets:
        if x <= upper:
            return rate
    return brackets[-1][1]


def _uk(P, g):
    pa = max(0.0, P["uk", "personal_allowance"] - max(0.0, (g - P["uk", "taper_start"]) / 2))
    tax = progressive(max(0.0, g - pa), P["uk", "brackets"])
    return tax, progressive(g, P["uk", "nic"])


def _us_federal(P, g):
    tax = progressive(max(0.0, g - P["us", "standard_deduction"]), P["us", "brackets"])
    social = (P["us", "social_security"] * min(g, P["us", "social_security_base"]) + P["us", "medicare"] * g
              + P["us", "additional_medicare"] * max(0.0, g - P["us", "additional_medicare_threshold"]))
    return tax, social


def _new_york_state(P, g):
    """New York State tax with the benefit recapture approximated: once income exceeds the recapture start, the tax
    moves over 50,000 of income from its value at the bracket's start (all lower income at the previous bracket's flat
    rate) to the bracket's flat rate on all taxable income; continuous at every bracket edge."""
    ti = max(0.0, g - P["ny", "standard_deduction"])
    br = P["ny", "brackets"]
    sched = progressive(ti, br)
    if g <= P["ny", "recapture_start"]:
        return sched
    rate = _rate_at(ti, br)
    edges = [0.0] + [u for u, _ in br[:-1]]
    k = max(i for i, e in enumerate(edges) if e < ti or i == 0)
    lower, prev = edges[k], (br[k - 1][1] if k > 0 else None)
    if lower <= P["ny", "recapture_start"] or prev is None:
        start, t0 = P["ny", "recapture_start"], sched
    else:
        start, t0 = lower, prev * lower + rate * (ti - lower)
    w = min(1.0, max(0.0, (g - start) / P["ny", "recapture_phase"]))
    return t0 + w * (rate * ti - t0)


def _nl(P, g, expat):
    taxable = g - (P["nl", "expat_share"] * min(g, P["nl", "expat_cap"]) if expat else 0.0)
    tax = progressive(taxable, P["nl", "brackets"])
    gen = max(0.0, P["nl", "general_credit"] - P["nl", "general_credit_rate"]
              * max(0.0, taxable - P["nl", "general_credit_start"]))
    lab = max(0.0, P["nl", "labour_credit"] - P["nl", "labour_credit_rate"]
              * max(0.0, taxable - P["nl", "labour_credit_start"]))
    return max(0.0, tax - gen - lab), 0.0  # national insurance premiums are inside the box 1 rates


def _ch_federal(P, taxable):
    t = math.floor(taxable / 100.0) * 100.0
    if t >= P["ch", "federal_flat_above"]:
        return P["ch", "federal_flat_rate"] * t
    pts = P.fed_points
    if t < pts[0][0]:
        return 0.0
    i = bisect.bisect_right([x for x, _ in pts], t) - 1
    (x0, y0), (x1, y1) = pts[i], pts[min(i + 1, len(pts) - 1)]
    return y0 if x1 == x0 else y0 + (y1 - y0) * (t - x0) / (x1 - x0)


def _zurich(P, g):
    social = P["ch", "ahv"] * g + P["ch", "alv"] * min(g, P["ch", "alv_ceiling"])
    taxable = g - social
    simple = progressive(taxable, P["zh", "brackets"])
    return simple * P["zh", "multiplier"] + _ch_federal(P, taxable), social


def _sg(P, g):
    return progressive(g, P["sg", "brackets"]), 0.0


def _hk(P, g):
    prog = progressive(max(0.0, g - P["hk", "basic_allowance"]), P["hk", "brackets"])
    std = progressive(g, P["hk", "standard_rates"])
    return min(prog, std), min(P["hk", "mpf_rate"] * g, P["hk", "mpf_cap"])


def net_local(P, location, g, expat=False):
    if location == "london":
        tax, social = _uk(P, g)
    elif location == "new_york":
        tax, social = _us_federal(P, g)
        ti = max(0.0, g - P["ny", "standard_deduction"])
        tax += _new_york_state(P, g) + progressive(ti, P["nyc", "brackets"])
    elif location == "chicago":
        tax, social = _us_federal(P, g)
        tax += P["il", "rate"] * g
    elif location == "amsterdam":
        tax, social = _nl(P, g, expat)
    elif location == "zurich":
        tax, social = _zurich(P, g)
    elif location == "singapore":
        tax, social = _sg(P, g)
    elif location == "hong_kong":
        tax, social = _hk(P, g)
    elif location == "dubai":
        tax, social = 0.0, 0.0
    else:
        raise KeyError(location)
    return {"tax": tax, "social": social, "net": g - tax - social}


def local_per_usd(P, location):
    cur = CURRENCY[location]
    if cur == "usd":
        return 1.0
    per_eur = 1.0 if cur == "eur" else P["fx", f"{cur}_per_eur"]
    return per_eur / P["fx", "usd_per_eur"]


def net_usd(P, location, gross_usd, expat=False):
    k = local_per_usd(P, location)
    r = net_local(P, location, gross_usd * k, expat)
    out = {key: v / k for key, v in r.items()}
    out["avg_rate"] = 1.0 - out["net"] / gross_usd
    return out


def marginal(P, location, gross_usd, step=1000.0, expat=False):
    a = net_usd(P, location, gross_usd - step, expat)["net"]
    b = net_usd(P, location, gross_usd, expat)["net"]
    return 1.0 - (b - a) / step
