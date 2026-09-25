"""Acceptance tests of firm.researchlog."""
import dataclasses
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_researchlog import ResearchLog, annual_to_period


def _log(tmp_path=None):
    log = ResearchLog(tmp_path / "log.jsonl" if tmp_path else None)
    log.register("rev", "overnight gaps revert: liquidity providers are paid to absorb them", "2026-01-05T09:00")
    for k in range(5):
        log.trial("rev", {"lookback": k + 1}, {"sr": 0.1 * k}, f"2026-01-05T10:0{k}")
    return log


def test_chain_intact_and_counted():
    log = _log()
    assert log.verify() == -1 and log.trial_count("rev") == 5 and not log.post_hoc("rev")
    assert log.metric("rev", "sr") == pytest.approx([0.0, 0.1, 0.2, 0.3, 0.4])


def test_tampering_is_detected():
    log = _log()
    e = log.entries[2]
    log.entries[2] = dataclasses.replace(e, body={**e.body, "metrics": {"sr": 9.9}})
    assert log.verify() == 2


def test_post_hoc_family_and_single_hypothesis():
    log = ResearchLog()
    log.trial("mom", {"lb": 12}, {"sr": 1.0}, "2026-02-01")
    log.register("mom", "written after the chart", "2026-02-02")
    assert log.post_hoc("mom")
    with pytest.raises(ValueError):
        log.register("mom", "again", "2026-02-03")


def test_persistence_roundtrip(tmp_path):
    _log(tmp_path)
    again = ResearchLog(tmp_path / "log.jsonl")
    assert again.verify() == -1 and again.trial_count("rev") == 5
    again.trial("rev", {"lookback": 9}, {"sr": 0.0}, "2026-01-06")
    assert ResearchLog(tmp_path / "log.jsonl").trial_count("rev") == 6


def test_deflation_grows_with_trials():
    log = ResearchLog()
    log.register("f", "h", "t0")
    sr = annual_to_period(1.5)
    values = []
    for n in (1, 10, 100):
        while log.trial_count("f") < n:
            log.trial("f", {}, {}, "t")
        values.append(log.deflated("f", sr, 504))
    assert values[0] > values[1] > values[2]
