"""Security (One Quant Book 15, chapter 29).

The firm's access policy is written as data -- twelve roles, a hundred people, five segregation-of-duties constraints
-- and checked for toxic combinations before and after a fix that splits the roles that concentrate duties. Venue API
keys are issued with scopes and a withdrawal allow-list, requests are signed with Book 13's HMAC signer, and a stolen
trading key is tried against the venue's checks. A year (250 trading days) of access logs for the hundred people records
the strategy-code files each reads a day; an insider copies a little more than usual every day from a random day on,
and is looked for with per-user robust scores, first as a single-day threshold and then as a CUSUM, both calibrated
on clean users to one false alarm a month (21 trading days) per hundred users.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/accessctl"))
import firm_accessctl as A  # noqa: E402

P = lambda r, a: (r, a)                                    # noqa: E731 - a permission
SOD = [(P("orders", "submit"), P("trades", "amend")),     # no correcting one's own trades
       (P("params", "propose"), P("params", "approve")),  # chapter 16's four eyes
       (P("code", "merge"), P("prod", "deploy")),         # chapter 27: nobody ships alone
       (P("venue_keys", "create"), P("wallet", "withdraw")),  # key makers move no money
       (P("payments", "create"), P("payments", "release"))]

BEFORE = {
    "trader": {P("orders", "submit"), P("positions", "read"), P("trades", "amend")},
    "quant researcher": {P("code", "read"), P("code", "merge"), P("data", "read"), P("params", "propose")},
    "developer": {P("code", "read"), P("code", "merge"), P("prod", "deploy")},
    "site reliability": {P("prod", "deploy"), P("prod", "read"), P("venue_keys", "create"), P("wallet", "withdraw")},
    "risk manager": {P("positions", "read"), P("params", "approve"), P("limits", "set")},
    "operations": {P("trades", "amend"), P("payments", "create"), P("payments", "release")},
    "compliance": {P("logs", "read"), P("positions", "read")},
    "treasury": {P("payments", "release"), P("wallet", "withdraw")},
    "head of desk": {P("orders", "submit"), P("params", "propose"), P("params", "approve"), P("limits", "set")},
    "data engineer": {P("data", "read"), P("data", "write")},
    "auditor": {P("logs", "read")},
    "administrator": {P("prod", "read"), P("logs", "read")},
}
AFTER = {**BEFORE,
         "trader": {P("orders", "submit"), P("positions", "read")},
         "developer": {P("code", "read"), P("code", "merge")},
         "release manager": {P("prod", "deploy")},
         "site reliability": {P("prod", "deploy"), P("prod", "read"), P("venue_keys", "create")},
         "operations": {P("trades", "amend"), P("payments", "create")},
         "head of desk": {P("orders", "submit"), P("params", "propose"), P("limits", "set")}}

HEADCOUNT = {"trader": 20, "quant researcher": 25, "developer": 20, "site reliability": 6, "risk manager": 6,
             "operations": 8, "compliance": 4, "treasury": 2, "head of desk": 3, "data engineer": 3, "auditor": 1,
             "administrator": 2}
DUAL = {"u020": "risk manager", "u021": "risk manager", "u022": "risk manager"}   # quants who also approve


def users(after: bool = False) -> dict:
    out, n = {}, 0
    for role, k in HEADCOUNT.items():
        for _ in range(k):
            out[f"u{n:03d}"] = {role}
            n += 1
    for u, extra in DUAL.items():
        out[u] = out[u] | {extra}
    if after:                                  # the fix also removes the second roles and names a release manager
        for u in DUAL:
            out[u] = {sorted(out[u] - {DUAL[u]})[0]}
        out["u045"] = {"release manager"}
    return out


def policies() -> dict:
    before = A.Policy(BEFORE, users(), sod=SOD)
    after = A.Policy(AFTER, users(after=True), sod=SOD)
    return {"before": before, "after": after}


def toxic_summary() -> dict:
    out = {}
    for name, p in policies().items():
        out[name] = {"roles": p.toxic_roles(), "users": p.toxic_users()}
    return out


# ------------------------------------------------------------ venue keys
def stolen_key_attempts() -> list[tuple]:
    keys = {"k-trade": A.VenueKey("k-trade", "s3cr3t-trade", frozenset({"read", "trade"})),
            "k-wd": A.VenueKey("k-wd", "s3cr3t-wd", frozenset({"withdraw"}), frozenset({"addr-custody-1"}))}
    t = 1_000.0
    tries = [("trade with the trading key", A.request(keys["k-trade"], "trade", {"qty": 100}, t)),
             ("withdraw with the trading key", A.request(keys["k-trade"], "withdraw", {"address": "addr-x"}, t)),
             ("withdraw to an outside address", A.request(keys["k-wd"], "withdraw", {"address": "addr-x"}, t)),
             ("withdraw to the custodian", A.request(keys["k-wd"], "withdraw", {"address": "addr-custody-1"}, t))]
    forged = dict(tries[0][1], sig="00" * 32)
    replay = tries[0][1]
    out = [(name, *A.verify(keys, req, t + 1)) for name, req in tries]
    out.append(("forged signature", *A.verify(keys, forged, t + 1)))
    out.append(("replayed a minute later", *A.verify(keys, replay, t + 60)))
    return out


def exposure_days(rotation_days: float) -> float:
    """Expected days a leaked secret stays valid when it leaks at a uniform time and is rotated every period."""
    return rotation_days / 2


# ------------------------------------------------------------ insider detection
N_USERS, N_DAYS, WINDOW, GAP = 100, 250, 30, 60
FA_PER_USER_DAY = 1 / (21 * 100)                 # one false alarm a month per hundred users
K = 0.5


def access_logs(seed: int = 29) -> np.ndarray:
    """Files of strategy code read a day, per user: each user's own level, weekly rhythm, noise."""
    rng = np.random.default_rng(seed)
    level = np.exp(rng.normal(np.log(40), 0.6, N_USERS))
    week = 1 + 0.15 * np.sin(2 * np.pi * np.arange(N_DAYS) / 5)
    noise = np.exp(rng.normal(0, 0.25, (N_USERS, N_DAYS)))
    return level[:, None] * week[None, :] * noise


def statistics(x: np.ndarray, k: float = K) -> dict:
    """Four detectors: a single-day threshold and a CUSUM, each on a trailing baseline (the last
    30 days) and on a lagged one (30 days ending 60 days earlier)."""
    out = {}
    for base, gap in (("trailing", 0), ("lagged", GAP)):
        z = A.robust_scores(np.log(x), WINDOW, gap)
        out[f"single day, {base}"] = z
        out[f"CUSUM, {base}"] = A.cusum(z, k)
    return out


def thresholds(seed: int = 29, k: float = K) -> dict:
    stats = statistics(access_logs(seed), k)
    return {name: A.calibrate(s, FA_PER_USER_DAY, WINDOW + GAP) for name, s in stats.items()}


def plant(x: np.ndarray, user: int, start: int, extra: float) -> np.ndarray:
    y = x.copy()
    y[user, start:] *= 1 + extra                 # a little more than usual, every day
    return y


def delays(extra: float, trials: int = 20, seed: int = 29, h: dict | None = None, k: float = K) -> dict:
    """For each detector: how many of `trials` planted insiders are flagged (on or after the day
    their copying starts), and the median days to the flag among those."""
    x, h = access_logs(seed), h or thresholds(seed, k)
    rng = np.random.default_rng(seed + 1)
    got = {name: [] for name in h}
    for _ in range(trials):
        u, start = int(rng.integers(N_USERS)), int(rng.integers(100, 150))
        stats = statistics(plant(x, u, start, extra)[u:u + 1], k)
        for name, s in stats.items():
            d = A.first_alarm(s[0], h[name], start)
            if d is not None:
                got[name].append(d)
    return {name: (len(v), float(np.median(v)) if v else float("nan")) for name, v in got.items()}


EXTRAS = (0.05, 0.1, 0.2, 0.3, 0.5, 1.0)
