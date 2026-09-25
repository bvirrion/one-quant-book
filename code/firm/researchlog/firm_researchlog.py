"""firm.researchlog -- the research log (build of One Quant Book 7, chapter 1).

An append-only, hash-chained registry of research trials. A hypothesis is registered in a family
before its trials; every trial records its parameters, code hash, data snapshot and metrics. The
log answers the two questions a review asks: how many trials stand behind a result, and did the
hypothesis come before the chart. Timestamps are supplied by the caller (ISO strings), never read
from the clock, so a log is reproducible. Stored as JSON lines; NumPy is not needed.

API (stable):
    ResearchLog(path=None)                 in memory, or appended to a JSON-lines file and reloaded
    .register(family, hypothesis, ts)      registers the family's hypothesis (once)
    .trial(family, params, metrics, ts, code_hash="", data_id="")   logs one trial -> Entry
    .trial_count(family)                   trials logged in the family
    .post_hoc(family)                      True if a trial was logged before the hypothesis
    .metric(family, name)                  list of one metric over the family's trials
    .verify()                              index of the first broken link, or -1 if the chain is intact
    .deflated(family, sr, n_obs, skew=0, kurt=3)   deflated Sharpe ratio with N = the logged trial count
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys
from dataclasses import asdict, dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "multitest"))
from firm_multitest import deflated_sharpe, expected_max_sr  # noqa: E402

GENESIS = "0" * 64


@dataclass(frozen=True)
class Entry:
    kind: str                      # "hypothesis" or "trial"
    family: str
    ts: str
    body: dict = field(default_factory=dict)
    prev: str = GENESIS
    digest: str = ""


def _digest(kind: str, family: str, ts: str, body: dict, prev: str) -> str:
    """SHA-256 of the canonical JSON of an entry and the previous digest: editing any past entry
    changes its digest and breaks every later link."""
    blob = json.dumps([kind, family, ts, body, prev], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


class ResearchLog:
    def __init__(self, path=None):
        self.path = pathlib.Path(path) if path else None
        self.entries: list[Entry] = []
        if self.path and self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    self.entries.append(Entry(**json.loads(line)))

    def _append(self, kind: str, family: str, ts: str, body: dict) -> Entry:
        prev = self.entries[-1].digest if self.entries else GENESIS
        e = Entry(kind, family, ts, body, prev, _digest(kind, family, ts, body, prev))
        self.entries.append(e)
        if self.path:
            with self.path.open("a") as f:
                f.write(json.dumps(asdict(e), sort_keys=True) + "\n")
        return e

    def register(self, family: str, hypothesis: str, ts: str) -> Entry:
        if any(e.kind == "hypothesis" and e.family == family for e in self.entries):
            raise ValueError(f"family {family!r} already has a hypothesis; open a new family")
        return self._append("hypothesis", family, ts, {"hypothesis": hypothesis})

    def trial(self, family: str, params: dict, metrics: dict, ts: str, code_hash: str = "",
              data_id: str = "") -> Entry:
        body = {"params": params, "metrics": metrics, "code_hash": code_hash, "data_id": data_id}
        return self._append("trial", family, ts, body)

    def _trials(self, family: str) -> list[Entry]:
        return [e for e in self.entries if e.kind == "trial" and e.family == family]

    def trial_count(self, family: str) -> int:
        return len(self._trials(family))

    def post_hoc(self, family: str) -> bool:
        for e in self.entries:
            if e.family == family:
                return e.kind == "trial"   # the family's first entry was a trial, not its hypothesis
        return False

    def metric(self, family: str, name: str) -> list[float]:
        return [float(e.body["metrics"][name]) for e in self._trials(family) if name in e.body["metrics"]]

    def verify(self) -> int:
        prev = GENESIS
        for i, e in enumerate(self.entries):
            if e.prev != prev or e.digest != _digest(e.kind, e.family, e.ts, e.body, e.prev):
                return i
            prev = e.digest
        return -1

    def deflated(self, family: str, sr: float, n_obs: int, skew: float = 0.0, kurt: float = 3.0) -> float:
        """Deflated Sharpe ratio (per-period sr) of the family's best trial: the benchmark is the
        expected maximum of N null Sharpe ratios, N the logged trial count and the null variance
        1 / n_obs (Book 4, chapter 12)."""
        n = max(1, self.trial_count(family))
        sr0 = expected_max_sr(n, 1.0 / n_obs) if n > 1 else 0.0
        return deflated_sharpe(sr, n_obs, skew, kurt, sr0)


def annual_to_period(sr_annual: float, periods: int = 252) -> float:
    return sr_annual / math.sqrt(periods)
