"""firm.vendormap -- the vendor map and a firm's stack as a dependency graph (build of One Quant Book 14, chapter 27).

Vendors are data: each inventory row names a category, a product type, a vendor, a product and the ledger row that
names it (data/vendor_inventory.csv). A firm's stack is a set of components, each supplied by one or more vendors
(or built in house), with a yearly spend and an estimated exit time, and a directed graph of what feeds what from the
market data in to the orders out. The measures: the Herfindahl--Hirschman index of spend by vendor; the components
whose failure alone cuts every path from data to orders; the vendors whose failure (every component they alone
supply) does; and a bill of materials for chapter 29. The example stack is synthetic.

API (stable):
    InventoryRow ; load_inventory(path) ; Component(name, vendors, spend, exit_weeks, critical=True)
    Stack(components, edges, source="data in", sink="orders out")
        .connected(removed=()) -> bool ; .single_points() -> [component] ; .vendor_points() -> [vendor]
        .hhi() -> float (0 to 10,000) ; .shares() -> {vendor: share of spend} ; .bom() -> [dict]
"""
import csv
import pathlib
from dataclasses import dataclass, field

HERE = pathlib.Path(__file__).resolve().parent
IN_HOUSE = "in house"


@dataclass(frozen=True)
class InventoryRow:
    category: str
    product_type: str
    vendor: str
    product: str
    source: str
    as_of: str


def load_inventory(path=HERE / "data" / "vendor_inventory.csv"):
    with open(path) as f:
        return [InventoryRow(r["category"], r["product_type"], r["vendor"], r["product"], r["source"], r["as_of"])
                for r in csv.DictReader(f)]


@dataclass(frozen=True)
class Component:
    name: str
    vendors: tuple
    spend: float
    exit_weeks: float
    critical: bool = True


@dataclass
class Stack:
    components: list
    edges: list
    source: str = "data in"
    sink: str = "orders out"
    by_name: dict = field(init=False)

    def __post_init__(self):
        self.by_name = {c.name: c for c in self.components}

    def connected(self, removed=()):
        """Is there a path from source to sink avoiding the removed components?"""
        gone = set(removed)
        seen, todo = {self.source}, [self.source]
        while todo:
            a = todo.pop()
            for x, y in self.edges:
                if x == a and y not in seen and y not in gone:
                    seen.add(y)
                    todo.append(y)
        return self.sink in seen

    def single_points(self):
        return [c.name for c in self.components if not self.connected((c.name,))]

    def vendor_points(self):
        """Vendors whose failure removes every component they alone supply and so cuts the path."""
        vendors = sorted({v for c in self.components for v in c.vendors if v != IN_HOUSE})
        out = []
        for v in vendors:
            gone = [c.name for c in self.components if c.vendors == (v,)]
            if gone and not self.connected(gone):
                out.append(v)
        return out

    def shares(self):
        total = sum(c.spend for c in self.components)
        s = {}
        for c in self.components:
            for v in c.vendors:
                s[v] = s.get(v, 0.0) + c.spend / len(c.vendors) / total
        return s

    def hhi(self):
        return sum((100 * x) ** 2 for v, x in self.shares().items() if v != IN_HOUSE)

    def bom(self):
        return [{"component": c.name, "vendors": ";".join(c.vendors), "spend": c.spend, "exit_weeks": c.exit_weeks}
                for c in self.components]
