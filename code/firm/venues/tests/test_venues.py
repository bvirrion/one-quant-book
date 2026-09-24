"""Acceptance tests of the Chapter 4 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_venues import Registry, Venue

ROOT = pathlib.Path(__file__).resolve().parents[4]
SAMPLE = str(ROOT / "data/markets-1/venues_sample.csv")


def v(mic, op=None, kind="exchange"):
    return Venue(mic, op or mic, "n", kind, "US", "USD", "flat")


def test_loads_the_sample():
    r = Registry.load(SAMPLE)
    assert len(r) == 10 and r.get("XNYS").name == "New York Stock Exchange"
    assert {x.mic for x in r.segments_of("XNYS")} == {"XNYS", "ARCX"}
    assert len(r.by_kind("exchange")) == 10


def test_rejects_bad_files_at_load_time():
    with pytest.raises(ValueError):
        Registry([v("XNYS"), v("XNYS")])
    with pytest.raises(ValueError):
        Registry([v("xnys")])
    with pytest.raises(ValueError):
        Registry([v("XNYS", kind="casino")])
    with pytest.raises(ValueError):
        Registry([v("ARCX", op="XNYS")])


def test_is_immutable():
    r = Registry([v("XNYS")])
    with pytest.raises(TypeError):
        r._by_mic["XNAS"] = v("XNAS")
