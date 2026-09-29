import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "venues"))
import firm_venues as fv  # noqa: E402
import firm_venuesites as vs  # noqa: E402


def test_registry_and_migration():
    r = vs.Registry.load()
    assert r.primary("XPAR", on="2022-06-01") == "basildon" and r.primary("XPAR", on="2022-06-06") == "bergamo"
    assert r.primary("XPAR") == "bergamo" and r.primary("XEUR") == "fr2"
    assert r.moves("XPAR") == [("2022-06-06", "basildon", "bergamo")]
    assert set(r.venues_at("bergamo")) == {"XPAR", "XAMS", "XBRU", "XLIS", "XMSM", "XOSL"}
    assert r.venues_at("basildon") == ["IFEU"] and "XPAR" in r.venues_at("basildon", on="2022-01-03")
    with pytest.raises(LookupError):
        r.primary("XXXX")


def test_nearest_and_join():
    r = vs.Registry.load()
    near = r.nearest("ld4")
    assert near[0][0] in ("XLON", "IFEU") and all(a[2] <= b[2] for a, b in zip(near, near[1:], strict=False))
    km = {m: k for m, _, k, _ in near}
    assert km["XLON"] < km["IFEU"] < km["XEUR"] < km["XPAR"]
    venues = fv.Registry.load(str(vs.ROOT / "data" / "markets-1" / "venues_sample.csv"))
    pairs = {v.mic: row.site for v, row in vs.join_venues(r, venues)}
    assert pairs["XNYS"] == "mahwah" and pairs["XEUR"] == "fr2" and pairs["XLON"] == "docklands"
    assert "XSWX" not in pairs                                   # not in Book 1's sample: skipped, not an error


def test_rules():
    site = vs.gm.Site("a", "A", "op", 0.0, 0.0, "x")
    ok = vs.VenueSite("TEST", "Test", "primary", "a", "", "", "F1", "2026-09-01")
    assert vs.Registry([ok], [site]).stale("2026-09-28") == []
    assert len(vs.Registry([ok], [site]).stale("2027-01-01")) == 1
    for bad in (ok.__class__(**{**ok.__dict__, "role": "hub"}), ok.__class__(**{**ok.__dict__, "site": "b"}),
                ok.__class__(**{**ok.__dict__, "source": ""}),
                ok.__class__(**{**ok.__dict__, "valid_from": "2026-02-01", "valid_to": "2026-01-01"})):
        with pytest.raises(ValueError):
            vs.Registry([bad], [site])
