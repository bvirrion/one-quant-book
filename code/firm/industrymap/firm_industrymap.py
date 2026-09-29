"""firm.industrymap -- the employer taxonomy and classification from public identifiers
(build of One Quant Book 17, chapter 1).

The taxonomy places an employer by five questions: whose capital it risks, who pays it, how long it holds a
position, what it sells, how large it is. Each business model belongs to one of four coarse groups:

    principal trading  : market maker, medium-frequency proprietary firm, crypto trading firm
    investment manager : systematic fund, multi-manager platform, discretionary fund, asset manager, asset owner
    bank               : bank markets division
    infrastructure     : exchange, broker, vendor, regulator

Two rules classify an entity from the outside, each returning a business model or UNKNOWN:
  - sic_class: the SEC's four-digit SIC code, which EDGAR assigns only to issuers of registered securities;
  - forms_class: the families of forms the entity files (broker-dealer annual reports X-17A-5 and FOCUS,
    13F holdings reports, issuer reports 10-K/10-Q/20-F, ATS-N), which private firms file too.
`combined` uses forms first and falls back to SIC for issuers. `score` compares a rule with the sourced truth
at the fine and the coarse level. Pure Python.

API (stable):
    MODELS, GROUP, BOOKS, UNKNOWN
    Entity(name, cik, sic, families, truth)
    load_sample(path) -> list[Entity]
    sic_class(sic) -> str ; forms_class(families) -> str
    by_sic(entity), by_forms(entity), combined(entity) -> str      rules on an Entity
    score(entities, rule, level="coarse") -> (correct, total)
    confusion(entities, rule, level="coarse") -> dict[(truth, guess)] -> count
"""
import csv
from collections import Counter
from dataclasses import dataclass

UNKNOWN = "unknown"

# business model -> (coarse group, whose capital, who pays, typical holding period)
MODELS = {
    "market maker": ("principal trading", "owners", "the spread and rebates", "seconds to hours"),
    "medium-frequency proprietary firm": ("principal trading", "owners", "trading profit", "minutes to days"),
    "crypto trading firm": ("principal trading", "owners", "spread and trading profit", "seconds to days"),
    "systematic fund": ("investment manager", "investors", "fees on assets and profits", "minutes to months"),
    "multi-manager platform": ("investment manager", "investors", "pass-through costs and profits", "days to months"),
    "discretionary fund": ("investment manager", "investors", "fees on assets and profits", "days to years"),
    "asset manager": ("investment manager", "clients", "fees on assets", "months to years"),
    "asset owner": ("investment manager", "beneficiaries", "its own budget", "years"),
    "bank": ("bank", "shareholders", "spread and client business", "minutes to months"),
    "exchange": ("infrastructure", "shareholders", "transaction and data fees", "none"),
    "broker": ("infrastructure", "shareholders", "commissions", "none"),
    "vendor": ("infrastructure", "shareholders", "licences", "none"),
    "regulator": ("infrastructure", "the public purse or levies", "fees and budget", "none"),
}
GROUP = {m: v[0] for m, v in MODELS.items()}

# where the series teaches each business model (book numbers)
BOOKS = {
    "market maker": (1, 10, 11, 13, 14), "medium-frequency proprietary firm": (7, 8, 12),
    "crypto trading firm": (3, 11, 14), "systematic fund": (4, 7, 8, 9, 12),
    "multi-manager platform": (8, 16), "discretionary fund": (9,), "asset manager": (1, 8),
    "asset owner": (1,), "bank": (2, 5, 6, 9), "exchange": (1, 10), "broker": (1, 10),
    "vendor": (14, 15), "regulator": (16,),
}

# SIC codes as EDGAR assigns them (issuers only). 6211 covers dealers, investment banks and some asset managers.
_SIC = {"6021": "bank", "6022": "bank", "6029": "bank", "6211": "market maker", "6200": "exchange",
        "6282": "asset manager", "6221": "market maker", "6199": "broker"}


@dataclass(frozen=True)
class Entity:
    name: str
    cik: int
    sic: str
    families: frozenset
    truth: str


def load_sample(path):
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            out.append(Entity(r["entity"], int(r["cik"]), r["sic"].strip(),
                              frozenset(r["form_families"].split()), r["truth"]))
    return out


def sic_class(sic):
    """Business model implied by an SIC code, UNKNOWN when there is none (every private filer)."""
    return _SIC.get(str(sic).strip(), UNKNOWN)


def forms_class(families):
    """Business model implied by the families of forms an entity files.

    A broker-dealer that is not an issuer is read as a principal trading firm; a filer of 13F holdings reports
    that is neither a broker-dealer nor an issuer is read as an investment manager (the rule cannot tell a
    systematic fund from a platform, so it answers the first investment-manager model). Issuers are left to SIC.
    """
    fam = set(families)
    if "issuer" in fam:
        return UNKNOWN
    if "broker-dealer" in fam:
        return "market maker"
    if "13F" in fam:
        return "systematic fund"
    return UNKNOWN


def by_sic(e):
    return sic_class(e.sic)


def by_forms(e):
    return forms_class(e.families)


def combined(e):
    g = forms_class(e.families)
    return g if g != UNKNOWN else sic_class(e.sic)


def _level(model, level):
    if model == UNKNOWN:
        return UNKNOWN
    return model if level == "fine" else GROUP[model]


def score(entities, rule, level="coarse"):
    """(correct, total): how many entities the rule places in their sourced class."""
    ok = sum(_level(rule(e), level) == _level(e.truth, level) for e in entities)
    return ok, len(entities)


def confusion(entities, rule, level="coarse"):
    return dict(Counter((_level(e.truth, level), _level(rule(e), level)) for e in entities))
