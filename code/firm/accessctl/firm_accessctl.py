"""firm.accessctl -- access policy, segregation of duties, secrets, venue credentials, insider detection (B15 ch. 29).

The access policy is data: roles grant (resource, action) pairs, users hold roles, deny rules override grants, and
segregation-of-duties constraints name pairs of permissions no single person may hold. The evaluator answers one
request; the checker lists every role and every user that holds a toxic combination. The vault keeps versioned
secrets with leases and a rotation period and reports what is about to expire. Venue credentials carry scopes and a
withdrawal allow-list, and every request is signed with Book 13's HMAC signer (firm.wsclient.Signer) and verified.
Access logs are scored per user against the user's own baseline (median and median absolute deviation of the
trailing days); a one-sided CUSUM of the scores accumulates small, persistent excesses that no single day shows;
thresholds are calibrated on users known to be clean for a stated false-alarm rate.

API (stable):
    Policy(roles {role: {(resource, action)}}, users {user: {role}}, deny {(user, res, action)}, sod [(perm, perm)])
        .allowed(user, resource, action) -> bool ; .permissions(user) -> set ; .toxic_roles() ; .toxic_users()
    Vault(): .put(name, value, at, ttl) ; .get(name, at) ; .rotate(name, value, at) ; .expiring(at, within)
    VenueKey(key_id, secret, scopes, allow_list) ; request(key, action, payload, at) -> dict ; verify(key, req, ...)
    robust_scores(x [users x days], window, gap=0) -> z ; cusum(z, k) -> S ; onsets(stat, h) ; calibrate(stat, rate)
    first_alarm(stat_row, h, start) -> day or None
"""
from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "wsclient"))
from firm_wsclient import Signer  # noqa: E402


# ------------------------------------------------------------ policy
@dataclass
class Policy:
    roles: dict
    users: dict
    deny: set = field(default_factory=set)
    sod: list = field(default_factory=list)

    def permissions(self, user: str) -> set:
        perms = set().union(*(self.roles[r] for r in self.users.get(user, ())))
        return {p for p in perms if (user, *p) not in self.deny}

    def allowed(self, user: str, resource: str, action: str) -> bool:
        return (resource, action) in self.permissions(user)

    def toxic_roles(self) -> list[tuple]:
        """Roles that alone hold both halves of a segregation-of-duties constraint."""
        return sorted((r, a, b) for r, perms in self.roles.items() for a, b in self.sod
                      if a in perms and b in perms)

    def toxic_users(self) -> list[tuple]:
        """Users who hold both halves, through one role or by combining several."""
        return sorted((u, a, b) for u in self.users for a, b in self.sod
                      if a in self.permissions(u) and b in self.permissions(u))


# ------------------------------------------------------------ secrets
class Vault:
    """Versioned secrets with leases: a secret is served only while its lease is valid."""

    def __init__(self):
        self.versions: dict = {}           # name -> [(version, value, issued, expires)]

    def put(self, name: str, value: str, at: float, ttl: float) -> int:
        vs = self.versions.setdefault(name, [])
        vs.append((len(vs) + 1, value, at, at + ttl))
        return len(vs)

    def get(self, name: str, at: float) -> str:
        v, value, issued, expires = self.versions[name][-1]
        if not issued <= at < expires:
            raise PermissionError(f"{name} v{v} is not valid at {at}")
        return value

    def rotate(self, name: str, value: str, at: float) -> int:
        _v, _val, issued, expires = self.versions[name][-1]
        return self.put(name, value, at, expires - issued)

    def expiring(self, at: float, within: float) -> list[str]:
        return sorted(n for n, vs in self.versions.items() if at <= vs[-1][3] < at + within)


# ------------------------------------------------------------ venue credentials
@dataclass
class VenueKey:
    key_id: str
    secret: str
    scopes: frozenset                  # e.g. {"read", "trade"}; "withdraw" only on dedicated keys
    allow_list: frozenset = frozenset()


def request(key: VenueKey, action: str, payload: dict, at: float) -> dict:
    body = json.dumps({"action": action, "at": at, **payload}, sort_keys=True)
    return {"key": key.key_id, "body": body, "sig": Signer(key.secret).sign(body)}


def verify(keys: dict, req: dict, at: float, max_age: float = 5.0) -> tuple[bool, str]:
    """What the venue checks: a known key, a valid signature, a fresh request, a scope that
    covers the action, and for withdrawals an address on the allow-list."""
    key = keys.get(req["key"])
    if key is None:
        return False, "unknown key"
    if Signer(key.secret).sign(req["body"]) != req["sig"]:
        return False, "bad signature"
    body = json.loads(req["body"])
    if not 0 <= at - body["at"] <= max_age:
        return False, "stale request"
    if body["action"] not in key.scopes:
        return False, "action outside the key's scope"
    if body["action"] == "withdraw" and body.get("address") not in key.allow_list:
        return False, "address not on the allow-list"
    return True, "ok"


# ------------------------------------------------------------ insider detection
def robust_scores(x: np.ndarray, window: int = 30, gap: int = 0) -> np.ndarray:
    """Each user-day against the user's own baseline: (x - median) / (1.4826 MAD) over the
    `window` days ending `gap` days before; a gap keeps a slow change out of its baseline.
    Days without a full baseline score 0."""
    n_users, n_days = x.shape
    z = np.zeros_like(x, dtype=float)
    for d in range(window + gap, n_days):
        past = x[:, d - gap - window:d - gap]
        med = np.median(past, axis=1)
        mad = 1.4826 * np.median(np.abs(past - med[:, None]), axis=1)
        z[:, d] = (x[:, d] - med) / np.maximum(mad, 1e-9)
    return z


def cusum(z: np.ndarray, k: float = 0.5) -> np.ndarray:
    """One-sided CUSUM per user: S_d = max(0, S_{d-1} + z_d - k)."""
    s = np.zeros_like(z, dtype=float)
    for d in range(1, z.shape[1]):
        s[:, d] = np.maximum(0.0, s[:, d - 1] + z[:, d] - k)
    return s


def onsets(stat: np.ndarray, h: float, start: int = 30) -> int:
    """Alarms raised: user-days on which the statistic crosses above h."""
    above = stat[:, start:] > h
    prev = np.concatenate([np.zeros((stat.shape[0], 1), dtype=bool), above[:, :-1]], axis=1)
    return int((above & ~prev).sum())


def calibrate(stat: np.ndarray, alarms_per_user_day: float, start: int = 30) -> float:
    """The lowest threshold at which clean users raise at most the stated alarms per user-day."""
    allowed = alarms_per_user_day * stat.shape[0] * (stat.shape[1] - start)
    lo, hi = 0.0, float(stat[:, start:].max()) + 1.0
    for _ in range(60):                             # bisection: onsets fall as h rises
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if onsets(stat, mid, start) > allowed else (lo, mid)
    return hi


def first_alarm(row: np.ndarray, h: float, start: int) -> int | None:
    hits = np.flatnonzero(row[start:] > h)
    return int(hits[0]) if hits.size else None
