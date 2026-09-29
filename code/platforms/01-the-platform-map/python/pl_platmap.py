"""The miniature firm's platform map (One Quant Book 15, chapter 1).

The firm built across the series, described as data for firm.platmap: its systems by layer, the datasets each one
is the system of record for, and the end-of-day batch that turns the day's fills, captures, vendor files and
market-data snapshots into the morning's reports. Times are minutes after the 16:00 close; the reports are due at
07:00 (900). Two configurations of the risk batch: dependency-driven (the fix) and a fixed 21:00 start (the one in
the chapter's hook). Two nights: the nominal one and the night the corporate-action file came at 21:30.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "platmap"))
from firm_platmap import Dataset, Job, PlatformMap, System, hhmm  # noqa: E402

DEADLINE = 900                                   # 07:00
LAYERS = ("external", "data", "trading", "positions", "risk", "post-trade", "control", "research")

SYSTEMS = [
    System("exchanges", "external", "venues"), System("data vendor", "external", "vendor"),
    System("clearing broker", "external", "broker"),
    System("tick capture", "data", "market data"), System("tick store", "data", "market data"),
    System("reference data", "data", "market data"), System("snapshot service", "data", "quant dev"),
    System("order gateway", "trading", "trading tech"), System("position service", "positions", "trading tech"),
    System("pnl service", "positions", "trading tech"), System("pricing library", "risk", "quant dev"),
    System("risk grid", "risk", "risk tech"), System("trade capture", "post-trade", "operations tech"),
    System("reconciliation", "post-trade", "operations tech"), System("product control", "control", "finance"),
    System("surveillance", "control", "compliance tech"), System("regulatory reporting", "control", "compliance tech"),
    System("research platform", "research", "research tech"),
]


def datasets(marks_owner=("pricing library",)) -> list[Dataset]:
    return [
        Dataset("fills", "position service", "stream", ready=5),
        Dataset("capture", "tick capture", "stream", ready=5),
        Dataset("closing prices", "tick store", ready=20),
        Dataset("snapshot", "snapshot service", ready=45),
        Dataset("vendor reference", "reference data", ready=120),
        Dataset("vendor corporate actions", "reference data", ready=210),
        Dataset("clearing statement", "reconciliation", ready=330),
        Dataset("tick history", "tick store"),
        Dataset("security master", "reference data"),
        Dataset("marks", marks_owner if len(marks_owner) > 1 else marks_owner[0]),
        Dataset("positions", "position service"),
        Dataset("pnl", "pnl service"),
        Dataset("scenarios", "risk grid"),
        Dataset("risk report", "risk grid"),
        Dataset("booked trades", "trade capture"),
        Dataset("confirmations", "trade capture"),
        Dataset("breaks", "reconciliation"),
        Dataset("signed pnl", "product control"),
        Dataset("alerts", "surveillance"),
        Dataset("transaction reports", "regulatory reporting"),
        Dataset("features", "research platform"),
        Dataset("backtests", "research platform"),
    ]


def jobs(risk_start=None) -> list[Job]:
    return [
        Job("compact ticks", ("capture",), ("tick history",), 35),
        Job("golden copy", ("vendor reference", "vendor corporate actions"),
            ("security master",), 25),
        Job("end-of-day marks", ("closing prices", "snapshot"), ("marks",), 20),
        Job("positions", ("fills", "security master"), ("positions",), 20),
        Job("pnl", ("positions", "marks", "security master"), ("pnl",), 25),
        Job("scenarios", ("snapshot",), ("scenarios",), 40),
        Job("risk batch", ("positions", "marks", "scenarios", "security master"),
            ("risk report",), 360, start=risk_start),
        Job("trade capture", ("fills",), ("booked trades",), 30),
        Job("confirmations", ("booked trades",), ("confirmations",), 45),
        Job("reconciliation", ("positions", "clearing statement"), ("breaks",), 40),
        Job("pnl sign-off", ("pnl", "breaks"), ("signed pnl",), 30),
        Job("surveillance", ("tick history", "fills"), ("alerts",), 90),
        Job("transaction reports", ("booked trades", "security master"),
            ("transaction reports",), 45),
        Job("features", ("tick history", "security master"), ("features",), 120),
        Job("backtests", ("features",), ("backtests",), 360),
    ]


def firm(risk_start=None) -> PlatformMap:
    return PlatformMap(SYSTEMS, datasets(), jobs(risk_start))


def draft() -> PlatformMap:
    """The map as first drawn: two systems both claim the marks."""
    return PlatformMap(SYSTEMS, datasets(("pricing library", "product control")), jobs(300))


HOOK_NIGHT = {"vendor corporate actions": 330}          # the file came at 21:30


def latest_arrivals(m: PlatformMap, deadline: float = DEADLINE) -> dict[str, float]:
    """Latest arrival of each external input that still lets every job meet the deadline."""
    late = m.latest_starts(deadline)
    out = {}
    for d in m.datasets:
        if d.ready is not None:
            readers = [late[j.name] for j in m.jobs if d.name in j.inputs]
            out[d.name] = min(readers) if readers else deadline
    return out


def tables():
    nominal, fixed = firm(), firm(risk_start=300)
    return {
        "problems": draft().validate(),
        "nominal": nominal.schedule(),
        "chain": nominal.longest_chain(),
        "slack": nominal.slack(DEADLINE),
        "latest": latest_arrivals(nominal),
        "blast": nominal.blast_radius(),
        "fixed_nominal_stale": fixed.stale_reads(),
        "fixed_hook_stale": fixed.stale_reads(HOOK_NIGHT),
        "dep_hook": nominal.schedule(HOOK_NIGHT),
        "dep_hook_stale": nominal.stale_reads(HOOK_NIGHT),
    }


if __name__ == "__main__":
    t = tables()
    for k, v in t.items():
        print(k)
        if isinstance(v, dict):
            for a, b in v.items():
                print("   ", a, b, [hhmm(x) for x in b] if isinstance(b, tuple) else hhmm(b) if k != "blast" else "")
        else:
            for x in v:
                print("   ", x)
