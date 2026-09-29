"""One Quant Book 16, chapter 21: twenty services, fifteen engineers, two ways to draw the teams (illustrative).

Three desks (equities, futures, options) each run a strategy, an order gateway, a risk check, a market-data handler
and a pricing library; five shared services serve all three. Change frequencies and page rates are per week.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/teamtopo"))
import firm_teamtopo as tp  # noqa: E402

DESKS = ("equities", "futures", "options")
KINDS = {"strategy": (5.0, 0.3), "gateway": (1.0, 0.5), "risk": (0.5, 0.2), "md": (1.0, 0.6), "pricing": (2.0, 0.1)}
SHARED = {"security master": (0.5, 0.1), "post-trade": (1.0, 0.4), "monitoring": (1.0, 0.2), "deployment": (1.5, 0.3),
          "research platform": (2.0, 0.1)}


def services():
    out = [tp.Service(f"{d} {k}", *v) for d in DESKS for k, v in KINDS.items()]
    return out + [tp.Service(k, *v) for k, v in SHARED.items()]


def deps():
    e = []
    for d in DESKS:
        e += [(f"{d} strategy", f"{d} pricing"), (f"{d} strategy", f"{d} gateway"), (f"{d} strategy", f"{d} md"),
              (f"{d} pricing", f"{d} md"), (f"{d} gateway", f"{d} risk"), (f"{d} risk", "security master"),
              (f"{d} strategy", "research platform"), ("post-trade", f"{d} gateway"), (f"{d} gateway", "deployment"),
              (f"{d} strategy", "deployment"), ("monitoring", f"{d} gateway")]
    return e


def embedded():
    owner = {f"{d} {k}": d for d in DESKS for k in KINDS} | {k: "infrastructure" for k in SHARED}
    return tp.Design(owner, {"equities": 4, "futures": 4, "options": 4, "infrastructure": 3})


def central():
    owner = {}
    for d in DESKS:
        owner |= {f"{d} strategy": d, f"{d} pricing": d, f"{d} gateway": "gateways", f"{d} risk": "risk",
                  f"{d} md": "market data"}
    owner |= {k: "infrastructure" for k in SHARED}
    return tp.Design(owner, {"equities": 2, "futures": 2, "options": 2, "gateways": 2, "risk": 2, "market data": 2,
                             "infrastructure": 3})


def compare():
    s, e = services(), deps()
    return {"embedded": tp.report(s, e, embedded()), "central": tp.report(s, e, central())}


def after_move():
    """One engineer leaves the equities desk in the embedded design, one the gateway team in the central one, each to
    infrastructure."""
    s, e = services(), deps()
    return {"embedded": tp.report(s, e, tp.move(embedded(), "equities", "infrastructure")),
            "central": tp.report(s, e, tp.move(central(), "gateways", "infrastructure"))}


CONSOLIDATED = {"gateway": (1.5, 0.8), "risk": (0.8, 0.3), "md": (1.5, 0.9)}


def consolidated_services():
    out = [tp.Service(f"{d} {k}", *KINDS[k]) for d in DESKS for k in ("strategy", "pricing")]
    return out + [tp.Service(k, *v) for k, v in CONSOLIDATED.items()] + [tp.Service(k, *v) for k, v in SHARED.items()]


def consolidated_deps():
    e = [("gateway", "risk"), ("risk", "security master"), ("post-trade", "gateway"), ("gateway", "deployment"),
         ("monitoring", "gateway")]
    for d in DESKS:
        e += [(f"{d} strategy", f"{d} pricing"), (f"{d} strategy", "gateway"), (f"{d} strategy", "md"),
              (f"{d} pricing", "md"), (f"{d} strategy", "research platform"), (f"{d} strategy", "deployment")]
    return e


def consolidated():
    owner = {f"{d} {k}": d for d in DESKS for k in ("strategy", "pricing")}
    owner |= {k: "trading platform" for k in CONSOLIDATED} | {k: "infrastructure" for k in SHARED}
    return tp.Design(owner, {"equities": 3, "futures": 3, "options": 3, "trading platform": 3, "infrastructure": 3})


def compare_all():
    out = compare()
    out["consolidated"] = tp.report(consolidated_services(), consolidated_deps(), consolidated())
    return out
