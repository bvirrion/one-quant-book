"""Acceptance tests of firm.accessctl (One Quant Book 15, chapter 29)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_accessctl as A  # noqa: E402

SUB, AMEND, PROP, APPR = ("orders", "submit"), ("trades", "amend"), ("params", "propose"), ("params", "approve")


def test_policy_and_segregation():
    p = A.Policy({"trader": {SUB, AMEND}, "ops": {AMEND}, "quant": {PROP}, "risk": {APPR}},
                 {"ann": {"trader"}, "bob": {"quant", "risk"}, "cy": {"ops"}}, deny={("ann", "trades", "amend")},
                 sod=[(SUB, AMEND), (PROP, APPR)])
    assert p.allowed("ann", "orders", "submit") and not p.allowed("ann", "trades", "amend")    # denied
    assert p.toxic_roles() == [("trader", SUB, AMEND)]
    assert p.toxic_users() == [("bob", PROP, APPR)]            # through two roles; ann's deny removes hers


def test_vault():
    v = A.Vault()
    v.put("venue-key", "s1", at=0, ttl=90)
    assert v.get("venue-key", 10) == "s1" and v.expiring(80, 20) == ["venue-key"]
    with pytest.raises(PermissionError):
        v.get("venue-key", 95)
    assert v.rotate("venue-key", "s2", at=85) == 2 and v.get("venue-key", 95) == "s2" and v.expiring(80, 20) == []


def test_venue_key_checks():
    keys = {"k": A.VenueKey("k", "sec", frozenset({"trade"})),
            "w": A.VenueKey("w", "sec2", frozenset({"withdraw"}), frozenset({"good"}))}
    ok = A.request(keys["k"], "trade", {"qty": 1}, 100.0)
    assert A.verify(keys, ok, 101.0) == (True, "ok")
    assert A.verify(keys, ok, 200.0)[1] == "stale request"
    assert A.verify(keys, dict(ok, sig="0"), 101.0)[1] == "bad signature"
    assert A.verify(keys, dict(ok, key="z"), 101.0)[1] == "unknown key"
    assert A.verify(keys, A.request(keys["k"], "withdraw", {"address": "good"}, 100.0), 100.0)[0] is False
    assert A.verify(keys, A.request(keys["w"], "withdraw", {"address": "bad"}, 100.0), 100.0)[1].startswith("address")
    assert A.verify(keys, A.request(keys["w"], "withdraw", {"address": "good"}, 100.0), 100.0)[0] is True


def test_scores_cusum_calibration():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, (50, 200))
    x[0, 150:] += 2.0                                          # a persistent shift for user 0
    z = A.robust_scores(x, 30, gap=20)
    assert np.all(z[:, :50] == 0) and abs(np.median(z[1:, 50:])) < 0.1
    s = A.cusum(z, 0.5)
    h = A.calibrate(s[1:], 1 / 1000, start=50)
    assert A.onsets(s[1:], h, 50) <= 49 * 150 / 1000
    d = A.first_alarm(s[0], h, 150)
    assert d is not None and d < 40
    assert A.first_alarm(np.zeros(10), 1.0, 0) is None
