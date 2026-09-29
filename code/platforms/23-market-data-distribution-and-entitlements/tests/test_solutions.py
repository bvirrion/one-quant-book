"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 23 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_entitle as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/23-market-data-distribution-and-entitlements"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    ups = P.updates(seconds=30.0, n_inst=4)
    r = P.distribute(ups, "conflate")
    assert r["strategy"].delivered > 0 and r["research"].max_depth <= 4
    assert P.distribute(ups, "all")["research"].delivered == len(ups)


def test_fees_and_audit():
    assert [P.non_display_fee(n) for n in (0, 22, 39, 40, 99, 100, 250)] == [
        0.0, 9064.0, 16068.0, 16490.0, 16490.0, 32990.0, 75000.0]
    a = P.audit()
    assert (a["owed"], a["display_owed"], a["non_display_owed"]) == (258596.0, 22932.0, 235664.0)
    first, last = a["rows"][0], a["rows"][-1]
    assert (first.used, first.owed) == ({"display": 43, "non-display": 4}, 1900.0)
    assert (last.used, last.owed) == ({"display": 53, "non-display": 22}, 10156.0)
    assert round(a["under_pct"], 1) == 87.5
    assert P.audit({"display": 53, "non-display": 22})["owed"] == 0.0


def test_distribution_csv():
    rows = {(r["policy"], r["subscriber"]): r for r in _csv("distribution.csv")}
    assert rows[("all", "research")]["max_depth"] == "180267" and rows[("all", "research")]["max_age_ms"] == "1802671.6"
    assert rows[("all", "risk")]["mean_age_ms"] == "58.4" and rows[("all", "risk")]["max_age_ms"] == "2407.0"
    assert rows[("conflate", "research")]["delivered"] == "60012" and rows[("conflate", "research")]["max_age_ms"] == "133.7"
    assert rows[("conflate", "risk")]["max_age_ms"] == "32.2"
    assert [r["after_revocation"] for r in _csv("revocation.csv")] == ["0", "6005"]


@pytest.mark.reference
def test_full_distribution():
    ups = P.updates()
    assert len(ups) == 240267
    r = P.distribute(ups, "all")
    assert (r["research"].max_depth, round(r["research"].max_age, 1)) == (180267, 1802.7)
    c = P.distribute(ups, "conflate")
    assert (c["research"].delivered, c["risk"].delivered, c["screen"].denied) == (60012, 221364, 6005)
