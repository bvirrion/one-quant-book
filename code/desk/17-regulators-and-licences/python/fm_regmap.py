"""One Quant Book 16, chapter 17: querying the regulatory map for firms that add offices (information, not advice).

The map is data/desk/regmap.csv, each row sourced in the chapter's ledger. A profile is a set of (jurisdiction,
activity) pairs.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/regmap"))
import firm_regmap as rm  # noqa: E402

MAP = ROOT / "data/desk/regmap.csv"
LONDON = {("UK", "own_account_exchange"), ("UK", "hft")}
CHICAGO = {("US", "own_account_exchange"), ("US", "hft")}
HONG_KONG = {("HK", "own_account_exchange")}
PROFILES = {"London": LONDON, "London and Chicago": LONDON | CHICAGO,
            "London, Chicago and Hong Kong": LONDON | CHICAGO | HONG_KONG}
EU_MM = {("EU", "market_making"), ("EU", "hft")}


def rows():
    return rm.load(MAP)


def profiles():
    r = rows()
    out = {}
    for name, p in PROFILES.items():
        q = rm.query(r, p)
        out[name] = {"rows": q, "regimes": rm.regimes(q), "longest": rm.longest_decision(q),
                     "by_status": {s: sum(x["status"] == s for x in q) for s in rm.STATUSES}}
    return out


# Statutory maximum periods for a decision, in days (six months counted as 183): ledger F2, F5, F6.
PERIODS = (("UK: complete application", 183), ("UK: incomplete application", 365), ("EU: complete application", 183),
           ("US broker-dealer: grant or open proceedings", 45), ("US: proceedings concluded", 120),
           ("US: with the 90-day extension", 210))
