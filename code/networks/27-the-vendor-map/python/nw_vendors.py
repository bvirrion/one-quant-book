"""Chapter 27 of One Quant Book 14: a new firm's stack on the vendor map (firm.vendormap; the stack is synthetic).

    STACK                      the example firm's components, vendors, yearly spend (thousand USD) and exit times
    report(stack)              HHI, vendor shares, single points of failure (components and vendors)
    second_server_vendor()     the same stack with a second server vendor on half the servers
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "vendormap"))
import firm_vendormap as vm  # noqa: E402

C, IH = vm.Component, vm.IN_HOUSE
COMPONENTS = [
    C("colocation", ("Equinix",), 600, 26), C("cross-connects", ("Equinix",), 120, 12),
    C("layer-1 fan-out", ("Arista",), 90, 8), C("switches", ("Cisco",), 150, 8),
    C("ticker plant", ("Exegy",), 400, 20), C("in-house feed handlers", (IH,), 150, 0),
    C("strategy servers", ("Blackcore",), 250, 6), C("NICs", ("AMD",), 60, 4),
    C("execution gateway", (IH,), 300, 0),
    C("order management", ("Trading Technologies",), 350, 16, critical=False),
    C("grandmaster clocks", ("Meinberg",), 40, 4, critical=False),
    C("network analytics", ("Pico",), 200, 12, critical=False),
    C("microwave route", ("Quincy Data",), 480, 8, critical=False),
]
EDGES = [("data in", "colocation"), ("colocation", "cross-connects"), ("cross-connects", "layer-1 fan-out"),
         ("cross-connects", "switches"), ("layer-1 fan-out", "ticker plant"), ("switches", "ticker plant"),
         ("layer-1 fan-out", "in-house feed handlers"), ("switches", "in-house feed handlers"),
         ("ticker plant", "strategy servers"), ("in-house feed handlers", "strategy servers"),
         ("strategy servers", "NICs"), ("NICs", "execution gateway"), ("execution gateway", "orders out")]
STACK = vm.Stack(COMPONENTS, EDGES)


def report(stack=STACK):
    return {"hhi": stack.hhi(), "shares": stack.shares(), "components": stack.single_points(),
            "vendors": stack.vendor_points(), "spend": sum(c.spend for c in stack.components)}


def second_server_vendor():
    comps = [c for c in COMPONENTS if c.name != "strategy servers"] + [
        C("strategy servers", ("Blackcore", "Business Systems International"), 250, 6)]
    return vm.Stack(comps, EDGES)
