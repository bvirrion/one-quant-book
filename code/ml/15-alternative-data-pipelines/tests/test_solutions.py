"""Numbers gate: every numerical answer printed in Book 12, chapter 15 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_altdata as m  # noqa: E402
from firm_altdata import resolve  # noqa: E402


def test_world():
    w = m.world()
    n = w["panelists"]
    assert (round(100 * n[0, 0].sum() / n[0].sum()), round(100 * w["pop"][0].sum())) == (45, 30)
    assert (n[0].sum(), n[m.CHANGE].sum(), n[m.CHANGE].min()) == (50000, 30000, 1125)
    assert round(100 * n[m.CHANGE, 2].sum() / n[m.CHANGE].sum()) == 50 and round(100 * n[m.CHANGE, :, 1].sum() / 30000) == 75


def test_validation():
    _, _, st = m.ingest()
    assert st["rows"] == 36766
    assert st["rejects"] == {"missing": 121, "range": 69, "type": 64, "duplicate": 111} == m.planted_defects()
    assert st["held"] == [m.CENTS_QUARTER + 1]


def test_resolution():
    r = m.resolution_quality()
    assert (r["retailer strings"], r["exact matches"], r["wrong matches"]) == (600, 300, 0)
    assert r["retailer status"] == {"matched": 500, "review": 100, "none": 0}
    assert r["distractor status"] == {"matched": 0, "review": 6, "none": 4}
    al = {n: i for i, n in enumerate(m.world()["names"])}
    out = resolve(["BOREALIS 5120", "BOREALI RETA STR 313"], al)
    assert out["BOREALIS 5120"][2] == "review" and round(out["BOREALIS 5120"][1], 2) == 0.79
    assert out["BOREALI RETA STR 313"] == (0, 1.0, "matched")
    assert [n for n in m.world()["names"] if n.startswith("Borealis")] == ["Borealis Retail", "Borealis Stores",
                                                                           "Borealis Outfitters"]


def test_errors():
    e = {k: {p: round(v, 1) for p, v in d.items()} for k, d in m.error_summary().items()}
    assert e == {"raw": {"quarters 4-15": 3.3, "quarters 16-19": 22.5, "quarters 20-23": 2.7},
                 "raked": {"quarters 4-15": 1.7, "quarters 16-19": 2.7, "quarters 20-23": 2.6}}
    assert round(float(np.mean(m.errors("raked")[4:])), 1) == 2.1
    err, lost = m.errors_without_review()
    assert (round(err, 1), round(100 * lost, 1)) == (19.7, 18.4)


def test_backfill_and_ic():
    assert m.backfilled_quarters() == list(range(11))
    ic = {k: {p: round(v, 3) for p, v in d.items() if p != "live"} for k, d in m.ic_summary().items()}
    assert ic == {"raw": {"backfilled": 0.366, "live before the change": 0.391, "live after the change": 0.264},
                  "raked": {"backfilled": 0.480, "live before the change": 0.419, "live after the change": 0.412}}
    assert round(100 * (0.480 / 0.419 - 1)) == 15


def test_exercises():
    w, wc = m.rake_example()
    assert np.round(w, 2).tolist() == [[1.18, 0.72], [1.45, 0.89]]
    assert np.round(wc, 1).tolist() == [[35.5, 14.5], [14.5, 35.5]]
    assert round(2.4e9 / 23.9e6) == 100
