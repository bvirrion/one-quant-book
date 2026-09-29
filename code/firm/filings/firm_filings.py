"""firm.filings -- facts from filed accounts, with provenance (build of One Quant Book 17, chapter 11).

A filed accounts document is read as a list of facts: a concept, a value, a unit, a period, and where the fact came
from. Machine-readable filings carry the facts as tags: an inline-XBRL document (UK and EU accounts, US 10-K filings)
wraps each number of the human-readable page in an ix:nonFraction element whose attributes give its concept, its
context (entity, period, dimensions), its unit, a scale (power of ten), a sign and a display format. SEC's
company-facts API gathers a US issuer's XBRL facts into one JSON document, in which every period recurs once per
filing that reports it. Image-only filings are transcribed by hand into the same Fact rows, with the page.

The module parses both machine-readable forms with the standard library only, maps taxonomy concepts to the book's
short names, keeps every fact with its source and locator (page, context or accession) in a Snapshot, checks the
snapshot's own arithmetic (revenue less expenses must give the operating profit the filing states), and maps a
year's facts onto firm.firmecon's Statement. Privacy rule: concepts about a named director or a highest-paid person
are dropped at parse time unless asked for.

API (stable):
    Fact(entity, concept, value, unit, start, end, source, locator, note='', dims=())
    number(text, fmt='', scale=0, sign='') -> float          one displayed number to its value
    parse_ixbrl(text, entity='', source='', keep_private=False) -> list[Fact]
    companyfacts(doc, concepts, entity='', source='') -> list[Fact]   annual 10-K values, latest filing per period
    ALIASES, PRIVATE
    Snapshot(facts): load(path), save(path), get(entity, concept, end), series(entity, concept),
                     ends(entity), problems(), reconcile(entity, total, parts, tol)
    months(start, end) -> int
    per_head(snap, entity, num, den) -> list[(end, value)]
    to_statement(snap, entity, end, mapping, headcount=None) -> firm_firmecon.Statement
"""
import csv
import datetime as dt
import math
import pathlib
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "firmecon"))
import firm_firmecon as fe  # noqa: E402

# taxonomy concept (local name) -> the book's short name; anything absent keeps its own name
ALIASES = {
    "TurnoverRevenue": "Revenue", "Revenues": "Revenue", "Revenue": "Revenue",
    "AdministrativeExpenses": "AdministrativeExpenses",
    "OperatingProfitLoss": "OperatingProfit",
    "ProfitLossOnOrdinaryActivitiesBeforeTax": "ProfitBeforeTax",
    "ProfitLoss": "ProfitAfterTax", "NetIncomeLoss": "ProfitAfterTax",
    "StaffCostsEmployeeBenefitsExpense": "StaffCosts", "LaborAndRelatedExpense": "StaffCosts",
    "WagesSalaries": "WagesSalaries", "SocialSecurityCosts": "SocialSecurityCosts",
    "PensionCostsDefinedContributionPlan": "PensionCosts",
    "AverageNumberEmployeesDuringPeriod": "AverageEmployees",
    "OtherOperatingIncomeFormat1": "OtherOperatingIncome",
    "TradingGainsLosses": "TradingGains",
}
PRIVATE = re.compile(r"Director|HighestPaid|ChiefExecutive|KeyManagement|NamedExecutive", re.I)
FIELDS = ("entity", "concept", "start", "end", "value", "unit", "source", "locator", "note")


@dataclass(frozen=True)
class Fact:
    entity: str
    concept: str
    value: float
    unit: str
    start: str          # ISO date, '' for an instant
    end: str            # ISO date (period end or instant)
    source: str         # filing: URL or registry reference
    locator: str        # page, context id or accession number
    note: str = ""
    dims: tuple = field(default=())


def number(text: str, fmt: str = "", scale: int = 0, sign: str = "") -> float:
    """The value of one displayed number: format decides the separators, scale the power of ten, sign the sign."""
    t = re.sub(r"\s+", "", text or "")
    f = fmt.split(":")[-1].lower()
    if f in ("zerodash", "fixed-zero", "fixedzero") or t in ("-", "\u2013", "\u2014"):
        v = 0.0
    else:
        if f in ("numdotcomma", "num-comma-decimal", "numcommadecimal"):
            t = t.replace(".", "").replace(" ", "").replace(",", ".")
        else:  # numcommadot, num-dot-decimal, numspacedot and the default
            t = t.replace(",", "").replace(" ", "")
        t = t.strip("()")
        v = float(t) if t else 0.0
    v *= 10.0 ** int(scale or 0)
    return -v if sign == "-" else v


class _IX(HTMLParser):
    """Collect contexts, units and nonFraction facts; tag and attribute names arrive lower-cased."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.contexts, self.units, self.raw = {}, {}, []
        self._ctx = self._unit = None
        self._field = None
        self._stack = []  # open nonFraction elements: [attrs, text parts]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "xbrli:context":
            self._ctx = {"id": a.get("id"), "start": "", "end": "", "dims": []}
        elif tag == "xbrli:unit":
            self._unit = {"id": a.get("id"), "measures": []}
        elif tag in ("xbrli:startdate", "xbrli:enddate", "xbrli:instant", "xbrli:measure"):
            self._field = [tag, ""]
        elif tag in ("xbrldi:explicitmember", "xbrldi:typedmember") and self._ctx is not None:
            self._field = [tag, a.get("dimension", "") + "="]
        elif tag == "ix:nonfraction":
            self._stack.append([a, []])

    def handle_endtag(self, tag):
        if self._field and tag == self._field[0]:
            name, val = self._field[0], self._field[1].strip()
            if name == "xbrli:measure" and self._unit is not None:
                self._unit["measures"].append(val.split(":")[-1])
            elif name.startswith("xbrldi:") and self._ctx is not None:
                self._ctx["dims"].append(re.sub(r"\s+", "", val))
            elif self._ctx is not None:
                key = {"xbrli:startdate": "start", "xbrli:enddate": "end", "xbrli:instant": "end"}[name]
                self._ctx[key] = val
            self._field = None
        elif tag == "xbrli:context" and self._ctx:
            self.contexts[self._ctx["id"]] = self._ctx
            self._ctx = None
        elif tag == "xbrli:unit" and self._unit:
            self.units[self._unit["id"]] = "/".join(self._unit["measures"])
            self._unit = None
        elif tag == "ix:nonfraction" and self._stack:
            a, parts = self._stack.pop()
            text = "".join(parts)
            if self._stack:  # a nested fact's text is also its parent's text
                self._stack[-1][1].append(text)
            self.raw.append((a, text))

    def handle_data(self, data):
        if self._field is not None:
            self._field[1] += data
        if self._stack:
            self._stack[-1][1].append(data)


def parse_ixbrl(text: str, entity: str = "", source: str = "", keep_private: bool = False) -> list:
    """Every numeric fact of an inline-XBRL document; identical repeats (a number tagged twice) are kept once."""
    p = _IX()
    p.feed(text)
    out, seen = [], set()
    for a, shown in p.raw:
        local = a.get("name", "").split(":")[-1]
        if not keep_private and PRIVATE.search(local):
            continue
        ctx = p.contexts.get(a.get("contextref", ""), {"start": "", "end": "", "dims": []})
        if a.get("xsi:nil") == "true":
            continue
        v = number(shown, a.get("format", ""), int(a.get("scale", 0) or 0), a.get("sign", ""))
        key = (local, a.get("contextref"), v)
        if key in seen:
            continue
        seen.add(key)
        out.append(Fact(entity, ALIASES.get(local, local), v, p.units.get(a.get("unitref", ""), ""), ctx["start"],
                        ctx["end"], source, a.get("contextref", ""), local, tuple(ctx["dims"])))
    return out


def _days(start: str, end: str) -> int:
    return (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days


def companyfacts(doc: dict, concepts, entity: str = "", source: str = "") -> list:
    """Annual 10-K values (periods of 350 to 380 days) of the given concepts; for each period the latest filing wins."""
    out = []
    for taxonomy in doc.get("facts", {}).values():
        for concept in concepts:
            if concept not in taxonomy:
                continue
            for unit, vals in taxonomy[concept]["units"].items():
                best = {}
                for v in vals:
                    if v.get("form") != "10-K" or not v.get("start") or not 350 <= _days(v["start"], v["end"]) <= 380:
                        continue
                    k = (v["start"], v["end"])
                    if k not in best or v["filed"] > best[k]["filed"]:
                        best[k] = v
                for (s, e), v in sorted(best.items()):
                    out.append(Fact(entity or doc.get("entityName", ""), ALIASES.get(concept, concept), float(v["val"]),
                                    unit, s, e, source, v["accn"], concept))
    return out


def months(start: str, end: str) -> int:
    """Length of a reporting period in whole months (a 14-month first period is common)."""
    return round((_days(start, end) + 1) / 30.44)


class Snapshot:
    """Facts with provenance; lookups ignore dimensional facts (segments, categories)."""

    def __init__(self, facts=()):
        self.facts = list(facts)

    @classmethod
    def load(cls, *paths):
        facts = []
        for path in paths:
            with open(path) as f:
                for r in csv.DictReader(f):
                    facts.append(Fact(r["entity"], r["concept"], float(r["value"]), r["unit"], r["start"], r["end"],
                                      r["source"], r["locator"], r.get("note", "")))
        return cls(facts)

    def save(self, path):
        with open(path, "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(FIELDS)
            for x in sorted(self.facts, key=lambda x: (x.entity, x.end, x.concept)):
                w.writerow([x.entity, x.concept, x.start, x.end, repr(x.value) if x.value % 1 else int(x.value), x.unit,
                            x.source, x.locator, x.note])

    def _plain(self, entity, concept):
        return [x for x in self.facts if x.entity == entity and x.concept == concept and not x.dims]

    def get(self, entity, concept, end):
        vals = [x for x in self._plain(entity, concept) if x.end == end]
        return vals[0].value if vals else None

    def series(self, entity, concept):
        return sorted((x.end, x.value) for x in self._plain(entity, concept))

    def ends(self, entity):
        return sorted({x.end for x in self.facts if x.entity == entity and x.start})

    def problems(self):
        """Missing provenance, non-finite values, private concepts, and one period stated with two values."""
        out, seen = [], {}
        for x in self.facts:
            if not x.source or not x.locator:
                out.append(f"no provenance: {x.entity} {x.concept} {x.end}")
            if not math.isfinite(x.value):
                out.append(f"not finite: {x.entity} {x.concept} {x.end}")
            if PRIVATE.search(x.concept) or PRIVATE.search(x.note):
                out.append(f"private concept: {x.entity} {x.concept}")
            k = (x.entity, x.concept, x.start, x.end, x.dims)
            if k in seen and seen[k] != x.value:
                out.append(f"two values: {x.entity} {x.concept} {x.end} {seen[k]} {x.value}")
            seen.setdefault(k, x.value)
        return out

    def reconcile(self, entity, total, parts, tol=0.5):
        """Periods where total != sum(sign * part) beyond tol: [(end, stated, computed)]."""
        bad = []
        for end, stated in self.series(entity, total):
            vals = [self.get(entity, c, end) for c, _ in parts]
            if any(v is None for v in vals):
                continue
            comp = sum(s * v for (_, s), v in zip(parts, vals, strict=True))
            if abs(comp - stated) > tol:
                bad.append((end, stated, comp))
        return bad


def per_head(snap: Snapshot, entity: str, num: str, den: str) -> list:
    """num / den for every period end where both are stated."""
    out = []
    for end, v in snap.series(entity, num):
        d = snap.get(entity, den, end)
        if d:
            out.append((end, v / d))
    return out


def to_statement(snap: Snapshot, entity: str, end: str, mapping: dict, headcount: str | None = None):
    """firm.firmecon Statement for one period: mapping[line] = [(concept, sign), ...] over this snapshot's concepts."""
    row = {"year": int(end[:4])}
    for terms in mapping.values():
        for c, _ in terms:
            row[c] = snap.get(entity, c, end)
    if headcount:
        row[headcount] = snap.get(entity, headcount, end)
    return fe.statements([row], mapping, headcount=headcount)[0]
