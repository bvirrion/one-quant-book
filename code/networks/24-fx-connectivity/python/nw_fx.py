"""Chapter 24 of One Quant Book 14: a London liquidity provider's quotes at the FX sites (firm.fxlinks, model).

    SITES, LP, VENUE_SITES, ORIGINS     the sites of the dated venue table; the LP in London LD4
    EQUAL, BACKBONE                     route factors: every path 1.5 (chapter 19's specialist), or the LP's
                                        information path at 2.46 (chapter 19's backbone)
    staleness_table(paths)              quote staleness at each venue site for moves at each origin
    tokyo()                             the weekend problem's numbers for a Tokyo move and the Tokyo site
    caught_curves(holds)                share of informed requests the price check catches after each hold
    aggregator_windows()                how long each LP's quote stays stale at a Tokyo aggregator after a Tokyo move
    order_paths()                       a Tokyo trader's order to the EBS engines through the Tokyo gateway
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "fxlinks"))
import firm_fxlinks as fx  # noqa: E402

SITES = fx.sites()
LP = "ld4"
VENUE_SITES = ("ld4", "ny5", "ny6", "ty3", "sg1")
ORIGINS = ("ld4", "ny5", "ty3")
EQUAL = fx.Paths()
BACKBONE = fx.Paths(info=2.46)
HOLDS = tuple(range(0, 61))
STAGES = {"gateway": 0.02, "credit screen": 0.01, "match": 0.01}   # ms, assumptions


def staleness_table(paths=EQUAL):
    return {(o, v): fx.staleness_ms(o, LP, v, paths, SITES) for o in ORIGINS for v in VENUE_SITES}


def tokyo():
    floor = fx.one_way_ms("ty3", LP, 1.0, SITES)
    return {"floor": floor, "stale_equal": fx.staleness_ms("ty3", LP, "ty3", EQUAL, SITES),
            "stale_backbone": fx.staleness_ms("ty3", LP, "ty3", BACKBONE, SITES),
            "hold_equal": fx.hold_ms("ty3", LP, "ty3", EQUAL, SITES),
            "hold_backbone": fx.hold_ms("ty3", LP, "ty3", BACKBONE, SITES)}


def caught_curves(holds=HOLDS):
    return {name: fx.caught("ty3", LP, "ty3", p, holds, table=SITES) for name, p in (("equal", EQUAL),
                                                                                    ("backbone", BACKBONE))}


def aggregator_windows(lps=("ld4", "ny6", "ty3")):
    lags = {s: fx.one_way_ms("ty3", s, 1.5, SITES) + EQUAL.proc_ms + fx.one_way_ms(s, "ty3", 1.5, SITES) for s in lps}
    return fx.stale_window_ms(lags)


def order_paths():
    return {e: fx.order_path_ms("ty3", e, STAGES, 1.5, SITES) for e in ("ny5", "ld4")}
