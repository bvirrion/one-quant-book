import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_vendormap as vm  # noqa: E402


def test_inventory_rows_have_sources():
    rows = vm.load_inventory()
    assert len(rows) >= 10 and all(r.source.startswith("networks/") and r.as_of for r in rows)


def test_graph_and_measures():
    comps = [vm.Component("a", ("V",), 50.0, 4), vm.Component("b1", ("W",), 25.0, 2), vm.Component("b2", ("X",), 25.0, 2)]
    edges = [("data in", "a"), ("a", "b1"), ("a", "b2"), ("b1", "orders out"), ("b2", "orders out")]
    s = vm.Stack(comps, edges)
    assert s.connected() and s.single_points() == ["a"] and s.vendor_points() == ["V"]
    assert abs(s.hhi() - (50 ** 2 + 25 ** 2 + 25 ** 2)) < 1e-9
    assert len(s.bom()) == 3 and not s.connected(("b1", "b2"))


def test_in_house_is_not_a_vendor():
    comps = [vm.Component("a", (vm.IN_HOUSE,), 10.0, 0), vm.Component("b", ("V", "W"), 10.0, 1)]
    s = vm.Stack(comps, [("data in", "a"), ("a", "b"), ("b", "orders out")])
    assert s.vendor_points() == [] and s.hhi() == 25 ** 2 * 2
