"""Numbers gate: every number printed in Book 14, chapter 27 (text and solutions)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_vendors as n  # noqa: E402

vm = n.vm


def test_stack():
    r = n.report()
    assert round(r["hhi"]) == 1149 and r["spend"] == 3190
    assert r["components"] == ["colocation", "cross-connects", "strategy servers", "NICs", "execution gateway"]
    assert r["vendors"] == ["AMD", "Blackcore", "Equinix"]
    s = r["shares"]
    assert [round(100 * s[v], 1) for v in ("Equinix", "Quincy Data", vm.IN_HOUSE, "Exegy")] == [22.6, 15.0, 14.1, 12.5]
    assert sum(c.exit_weeks for c in n.COMPONENTS if c.name in r["components"]) == 48
    r2 = n.report(n.second_server_vendor())
    assert round(r2["hhi"]) == 1119 and r2["vendors"] == ["AMD", "Equinix"]


def test_exercises():
    C = vm.Component
    comps = [C(c.name, c.vendors, c.spend * 2 if "Equinix" in c.vendors else c.spend, c.exit_weeks, c.critical)
             for c in n.COMPONENTS]
    assert round(vm.Stack(comps, n.EDGES).hhi()) == 1782 and 2 * 720 == 1440 and 3190 + 720 == 3910
    comps2 = list(n.COMPONENTS) + [C("colocation B", ("operator B",), 600, 26), C("cross-connects B", ("operator B",), 120, 12)]
    e = list(n.EDGES) + [("data in", "colocation B"), ("colocation B", "cross-connects B"),
                         ("cross-connects B", "layer-1 fan-out"), ("cross-connects B", "switches")]
    s = vm.Stack(comps2, e)
    assert s.vendor_points() == ["AMD", "Blackcore"] and round(s.hhi()) == 1104
    assert len(vm.load_inventory()) == 16


def test_small_runs():
    assert n.STACK.connected() and not n.STACK.connected(("colocation",))
