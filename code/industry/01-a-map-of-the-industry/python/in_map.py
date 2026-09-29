"""One Quant Book 17, chapter 1: a map of the industry.

Reads two derived tables (data/industry/LICENSES.md gives the sources):
  - employer_sample.csv: 21 EDGAR entities with their SIC code (issuers only), the families of forms they
    file, and the business model their own publications state (the truth, ledger row per entity);
  - finra_firms.csv: FINRA-registered broker-dealers and SEC/state investment advisers, 2015-2024.
and classifies the sample with firm.industrymap's rules.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/industrymap"))
import firm_industrymap as im  # noqa: E402

DATA = ROOT / "data/industry"
RULES = {"SIC code": im.by_sic, "forms filed": im.by_forms, "forms, then SIC": im.combined}


def sample():
    return im.load_sample(DATA / "employer_sample.csv")


def accuracy():
    """{rule: {level: (correct, total)}} on the sample."""
    es = sample()
    return {k: {lv: im.score(es, r, lv) for lv in ("coarse", "fine")} for k, r in RULES.items()}


def misses(rule="forms, then SIC", level="coarse"):
    r = RULES[rule]
    return [e.name for e in sample() if im._level(r(e), level) != im._level(e.truth, level)]


def counts():
    """Truth classes in the sample and how many carry an SIC code."""
    es = sample()
    by = {}
    for e in es:
        by.setdefault(e.truth, [0, 0])
        by[e.truth][0] += 1
        by[e.truth][1] += bool(e.sic)
    return by


def finra():
    with open(DATA / "finra_firms.csv") as f:
        return [{k: (int(v) if v else None) for k, v in r.items()} for r in csv.DictReader(f)]


def finra_2024():
    """Broker-dealers, advisers-only and the proprietary/market-making segments at the end of 2024."""
    y = finra()[-1]
    with open(DATA / "finra_segments_2024.csv") as f:
        seg = list(csv.DictReader(f))
    prop = sum(int(r["firms"]) for r in seg if r["segment"] != "all segments")
    alls = sum(int(r["firms"]) for r in seg if r["segment"] == "all segments")
    return dict(bd=y["bd_only"] + y["dual"], ia_only=y["ia_only"], prop=prop, segmented=alls,
                small=y["small"], mid=y["mid"], large=y["large"])
