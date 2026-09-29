import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_lineage as fl  # noqa: E402


def g():
    x = fl.Graph()
    x.add_node(fl.Node("V", "venue", None, "A", "F1"))
    x.add_node(fl.Node("P", "firm", 1990, "A", "F2"))
    x.add_node(fl.Node("C", "firm", 2005, "B", "F3"))
    x.add_edge(fl.Edge("P", "V", "floor", "F2"))
    x.add_edge(fl.Edge("C", "P", "spun out of", "F3"))
    return x


def test_queries():
    x = g()
    assert x.by_place() == {"A": ["P"], "B": ["C"]} and x.by_decade() == {1990: 1, 2000: 1}
    assert x.children("V") == ["P"] and x.ancestors("C") == ["P", "V"] and x.unsourced() == []


def test_unsourced_rejected():
    x = g()
    with pytest.raises(ValueError):
        x.add_edge(fl.Edge("C", "V", "floor", ""))
    with pytest.raises(KeyError):
        x.add_edge(fl.Edge("C", "Z", "floor", "F9"))
