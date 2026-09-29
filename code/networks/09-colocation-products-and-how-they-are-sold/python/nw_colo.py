"""Chapter 9 of One Quant Book 14: pricing a colocation footprint from published fee schedules (firm.colobill).

    FOOTPRINTS            the chapter's footprints: cabinets at one venue, connections to another
    bills(term_months)    each footprint's monthly, one-time and annual cost
    firm_bill()           the problem's footprint: two cabinets and two ultra-low-latency connections
    coil(distances, longest)   delay the equalising coil adds to each cabinet
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "colobill"))
import firm_colobill as cb  # noqa: E402

CAB = [("uhd_cabinet", 1), ("cabinet_install", 1), ("power_install_p3", 1)]
FOOTPRINTS = {
    "one cabinet": ("nasdaq-ny11-4", CAB),
    "two cabinets": ("nasdaq-ny11-4", [(k, 2 * q) for k, q in CAB]),
    "four cabinets": ("nasdaq-ny11-4", [(k, 4 * q) for k, q in CAB] + [("pdu_p3", 4)]),
    "one 1Gb connection": ("miax-pearl", [("conn_1g", 1)]),
    "two 10Gb ULL": ("miax-pearl", [("ull_10g", 2)]),
    "two 10Gb ULL and DR": ("miax-pearl", [("ull_10g", 2), ("dr_10g", 1)]),
}


def bills(term_months=36):
    return {k: cb.bill(cb.SCHEDULES[s], fp, term_months) for k, (s, fp) in FOOTPRINTS.items()}


def firm_bill(term_months=36):
    a = cb.bill(cb.SCHEDULES["nasdaq-ny11-4"], [(k, 2 * q) for k, q in CAB], term_months)
    b = cb.bill(cb.SCHEDULES["miax-pearl"], [("ull_10g", 2)], term_months)
    return {"monthly": a["monthly"] + b["monthly"], "one_time": a["one_time"], "total_monthly": a["total_monthly"]
            + b["total_monthly"], "annual": a["annual"] + b["annual"]}


def coil(distances=(5, 20, 40, 60, 80, 100, 120, 140), longest=150):
    return [(d, cb.equalisation_ns(d, longest)) for d in distances]
