"""firm.lineage -- a sourced genealogy of trading firms (build of One Quant Book 17, chapter 3).

Nodes are firms and venues (a trading floor, an exchange); each carries a founding year when a source gives one, a
place, and the ledger row that sources it. Edges link a firm to a venue or to another firm ("founders traded on the
floor of", "spun out of", "acquired by"), each with its own ledger row. An edge without a source is not added: the
graph is only as dense as the public record.

API (stable):
    Node(name, kind, year, place, ledger) ; Edge(src, dst, relation, ledger)
    Graph.load(path) ; g.add_node(n) ; g.add_edge(e)
    g.firms() ; g.by_place() -> dict[place, list[name]] ; g.by_decade() -> dict[int, int]
    g.children(venue_or_firm) ; g.ancestors(name) ; g.unsourced() -> list[str]
"""
import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    name: str
    kind: str
    year: int | None
    place: str
    ledger: str


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    relation: str
    ledger: str


class Graph:
    def __init__(self):
        self.nodes, self.edges = {}, []

    @classmethod
    def load(cls, path):
        g = cls()
        with open(path) as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            g.add_node(Node(r["name"], r["kind"], int(r["year"]) if r["year"] else None, r["place"], r["ledger"]))
        for r in rows:
            if r["target"]:
                g.add_edge(Edge(r["name"], r["target"], r["relation"], r["ledger"]))
        return g

    def add_node(self, n):
        if not n.ledger:
            raise ValueError(f"node {n.name} has no source")
        self.nodes[n.name] = n

    def add_edge(self, e):
        if not e.ledger:
            raise ValueError(f"edge {e.src}->{e.dst} has no source")
        if e.src not in self.nodes or e.dst not in self.nodes:
            raise KeyError(f"edge {e.src}->{e.dst}: unknown node")
        self.edges.append(e)

    def firms(self):
        return [n for n in self.nodes.values() if n.kind == "firm"]

    def by_place(self):
        out = {}
        for n in self.firms():
            out.setdefault(n.place, []).append(n.name)
        return {k: sorted(v) for k, v in out.items()}

    def by_decade(self):
        out = {}
        for n in self.firms():
            if n.year is not None:
                d = n.year // 10 * 10
                out[d] = out.get(d, 0) + 1
        return dict(sorted(out.items()))

    def children(self, name):
        return sorted(e.src for e in self.edges if e.dst == name)

    def ancestors(self, name):
        seen, todo = [], [name]
        while todo:
            x = todo.pop()
            for e in self.edges:
                if e.src == x and e.dst not in seen:
                    seen.append(e.dst)
                    todo.append(e.dst)
        return seen

    def unsourced(self):
        """Firms with no edge to a venue or firm: their origin is not in the public record used."""
        linked = {e.src for e in self.edges}
        return sorted(n.name for n in self.firms() if n.name not in linked)
