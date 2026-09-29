"""One Quant Book 17, chapter 2: profiles of proprietary market makers from public sources only.

data/industry/profiles/facts.csv holds one sourced fact per row (firm.profiles.Fact); the ledger rows it cites are
read from sources/industry/02-*.md, so a fact whose ledger row is missing fails validation.
"""
import csv
import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/profiles"))
import firm_profiles as fp  # noqa: E402

DATA = ROOT / "data/industry"
LEDGER = ROOT / "sources/industry/02-proprietary-market-makers-and-high-frequency-firms.md"
FIELDS = ["founded", "employees", "offices", "revenue", "products"]
LISTED = {"Virtu Financial"}
TODAY = dt.date(2026, 9, 29)


def facts():
    return fp.load_facts(DATA / "profiles/facts.csv")


def ledger_ids():
    return set(re.findall(r"^\| (F\d+) \|", LEDGER.read_text(), re.M))


def check():
    return fp.problems(facts(), ledger_ids(), TODAY)


def coverage():
    return {k: len(v) for k, v in fp.coverage(facts(), set(FIELDS)).items()}


def gap():
    return fp.gap(facts(), set(FIELDS), LISTED)


def cme():
    with open(DATA / "cme_venue_adv.csv") as f:
        return [{k: int(v) for k, v in r.items()} for r in csv.DictReader(f)]


def cme_shares(year=2025):
    r = next(x for x in cme() if x["year"] == year)
    return {k: r[k] / r["total"] for k in ("globex", "open_outcry", "privately_negotiated")}


def jse():
    """Jane Street Europe group, 2025 against 2024 ($ thousands, transcribed from its accounts)."""
    rev = (642985, 995769)
    pat = (437356, 654912)
    eq = (3058914, 2656690)
    return dict(rev_change=rev[0] / rev[1] - 1, margin=(pat[0] / rev[0], pat[1] / rev[1]), eq_change=eq[0] / eq[1] - 1,
                roe=pat[0] / ((eq[0] + eq[1]) / 2))


def citadel_2023():
    ta, tl = 52344, 47651
    return dict(capital=ta - tl, leverage=ta / (ta - tl))
