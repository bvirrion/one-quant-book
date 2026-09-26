"""firm.riskctl -- risk controls for automated trading: limits, monitors, kill switch (One Quant Book 11, ch. 27).

The policy side of the firm's pre-trade gate. One Quant Book 13's firm.riskgate is the nanosecond implementation and
replays these limits (its `from_riskctl` reads the "riskgate" section that `export` writes). This module owns the
limits hierarchy, its validation, the post-trade monitors (loss, position, message rate) with their kill actions,
the kill switch's state and audit log, and the chapter's runaway and normal-day simulations.

LIMITS SCHEMA (stable; version 1). Money in dollars, prices in dollars, quantities in shares, times in nanoseconds:
    {"version": 1,
     "gate": {"max_age_ns", "ref_max_age_ns", "dup_ns"},                 # snapshot and reference freshness
     "firm": {"max_gross_usd", "max_loss_usd", "max_msgs_per_s"},
     "desks": {name: {"max_gross_usd", "max_loss_usd"}},
     "strategies": {name: {"desk", "rate", "burst", "max_open", "max_loss_usd", "max_position_usd"}},
     "instruments": {locate: {"collar_bp", "max_qty", "max_notional_usd", "max_long", "max_short"}}}
Rules: every strategy names an existing desk; a desk's gross and loss limits do not exceed the firm's; every number
is positive. `to_riskgate` maps it to firm.riskgate's schema: notional and gross in price units of 1e-4 dollars
(integers), rate and burst in orders a second, instrument keys as integers, the same version.

API (stable):
    validate(limits) -> list[str]                  the rules above; an empty list is a valid snapshot
    to_riskgate(limits) -> dict                    firm.riskgate's schema
    export(limits) -> dict                         {"riskctl": limits, "riskgate": to_riskgate(limits)}
    KillSwitch()                                   .kill(t, level, name, action, reason), .unkill(t, level, name),
                                                   .blocks(strategy, desk) -> bool,
                                                   .audit [(t, event, level, name, text)]
    Monitor(limits, switch)                        post-trade: .on_fill(t, strat, instr, qty, price),
                                                   .mark(t, prices), .on_message(t, strat) -> kill actions
    runaway(controls, seconds, ...) -> dict        the loss and stop time of a 2012-shaped runaway under the controls
    normal_days(controls, n, seed) -> dict         false alarms of the same controls on ordinary days
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

SCALE = 10_000                                  # riskgate price units per dollar


def validate(d: dict) -> list[str]:
    errs = []
    if d.get("version") != 1:
        errs.append("version must be 1")
    firm = d.get("firm", {})
    for k in ("max_gross_usd", "max_loss_usd", "max_msgs_per_s"):
        if not firm.get(k, 0) > 0:
            errs.append(f"firm.{k} must be positive")
    for name, desk in d.get("desks", {}).items():
        for k in ("max_gross_usd", "max_loss_usd"):
            if not desk.get(k, 0) > 0:
                errs.append(f"desk {name}.{k} must be positive")
            elif desk[k] > firm.get(k, math.inf):
                errs.append(f"desk {name}.{k} exceeds the firm's")
    for name, s in d.get("strategies", {}).items():
        if s.get("desk") not in d.get("desks", {}):
            errs.append(f"strategy {name} names an unknown desk")
        for k in ("rate", "burst", "max_open", "max_loss_usd", "max_position_usd"):
            if not s.get(k, 0) > 0:
                errs.append(f"strategy {name}.{k} must be positive")
    for loc, ins in d.get("instruments", {}).items():
        for k in ("collar_bp", "max_qty", "max_notional_usd", "max_long", "max_short"):
            if not ins.get(k, 0) > 0:
                errs.append(f"instrument {loc}.{k} must be positive")
    return errs


def to_riskgate(d: dict) -> dict:
    g = d["gate"]
    return {"version": d["version"], "max_age_ns": int(g["max_age_ns"]), "ref_max_age_ns": int(g["ref_max_age_ns"]),
            "dup_ns": int(g.get("dup_ns", 0)),
            "firm": {"max_gross": int(d["firm"]["max_gross_usd"] * SCALE)},
            "desks": {k: {"max_gross": int(v["max_gross_usd"] * SCALE)} for k, v in d["desks"].items()},
            "strategies": {k: {"desk": v["desk"], "rate": int(v["rate"]), "burst": int(v["burst"]),
                               "max_open": int(v["max_open"])} for k, v in d["strategies"].items()},
            "instruments": {int(k): {"collar_bp": int(v["collar_bp"]), "max_qty": int(v["max_qty"]),
                                     "max_notional": int(v["max_notional_usd"] * SCALE), "max_long": int(v["max_long"]),
                                     "max_short": int(v["max_short"])} for k, v in d["instruments"].items()}}


def export(d: dict) -> dict:
    errs = validate(d)
    if errs:
        raise ValueError("; ".join(errs))
    return {"riskctl": d, "riskgate": to_riskgate(d)}


@dataclass
class KillSwitch:
    killed: dict = field(default_factory=dict)          # (level, name) -> action
    audit: list = field(default_factory=list)

    def kill(self, t: float, level: str, name: str, action: str, reason: str) -> None:
        if (level, name) not in self.killed:
            self.killed[(level, name)] = action
            self.audit.append((t, "kill", level, name, f"{action}: {reason}"))

    def unkill(self, t: float, level: str, name: str) -> None:
        if self.killed.pop((level, name), None) is not None:
            self.audit.append((t, "unkill", level, name, ""))

    def blocks(self, strategy: str, desk: str) -> bool:
        return any(k in self.killed for k in (("firm", ""), ("desk", desk), ("strategy", strategy)))


class Monitor:
    """Positions and P&L by strategy, desk and firm from fills and marks; loss limits kill with 'flatten', the firm's
    message rate kills the firm with 'cancel'."""

    def __init__(self, d: dict, switch: KillSwitch):
        self.d, self.sw = d, switch
        self.pos: dict = {}                               # (strat, instr) -> shares
        self.cash: dict = {}                              # strat -> dollars
        self.last: dict = {}                              # instr -> price
        self.msgs: list = []

    def on_fill(self, t: float, strat: str, instr: int, qty: int, price: float) -> None:
        self.pos[(strat, instr)] = self.pos.get((strat, instr), 0) + qty
        self.cash[strat] = self.cash.get(strat, 0.0) - qty * price
        self.last[instr] = price

    def pnl(self, strat: str) -> float:
        held = sum(q * self.last.get(i, 0.0) for (s, i), q in self.pos.items() if s == strat)
        return self.cash.get(strat, 0.0) + held

    def mark(self, t: float, prices: dict) -> list:
        self.last.update(prices)
        out = []
        desks: dict = {}
        for name, s in self.d["strategies"].items():
            p = self.pnl(name)
            desks[s["desk"]] = desks.get(s["desk"], 0.0) + p
            if p < -s["max_loss_usd"]:
                self.sw.kill(t, "strategy", name, "flatten", f"loss {p:.0f}")
                out.append(("strategy", name, "flatten"))
        for name, p in desks.items():
            if p < -self.d["desks"][name]["max_loss_usd"]:
                self.sw.kill(t, "desk", name, "flatten", f"loss {p:.0f}")
                out.append(("desk", name, "flatten"))
        if sum(desks.values()) < -self.d["firm"]["max_loss_usd"]:
            self.sw.kill(t, "firm", "", "flatten", "firm loss")
            out.append(("firm", "", "flatten"))
        return out

    def on_message(self, t: float, strat: str) -> list:
        self.msgs.append(t)
        while self.msgs and self.msgs[0] <= t - 1.0:
            self.msgs.pop(0)
        if len(self.msgs) > self.d["firm"]["max_msgs_per_s"]:
            self.sw.kill(t, "firm", "", "cancel", "message rate")
            return [("firm", "", "cancel")]
        return []


# ---------------------------------------------------------------- the chapter's simulations
RUNAWAY = {"orders_per_s": 1481.0, "shares": 100, "price": 40.0, "loss_per_share": 1.16, "gross_per_s": 2.46e6,
           "drift_per_min": 0.005}


def runaway(controls: dict, seconds: int = 2700, flatten_cost: float = 0.002, **kw) -> dict:
    """A runaway that, unchecked, sends 1,481 orders a second for 45 minutes and loses $1.16 a share traded (the
    SEC's order: 4 million executions, 397 million shares, $460 million). Controls (any subset):
        throttle: orders a second allowed        position: gross position limit (dollars)
        loss: loss limit (dollars), checked every mark_s seconds    capital: firm gross limit (dollars)
        collar_bp: price collar around a reference that drifts away at drift_per_min
        human_s: the time at which a person pulls the kill switch
    Returns the time the runaway was stopped, the loss by then, and which control stopped it; stopping flattens the
    gross position at flatten_cost of its value."""
    r = RUNAWAY | kw
    rate = min(r["orders_per_s"], controls.get("throttle", math.inf))
    loss_rate = rate * r["shares"] * r["loss_per_share"]
    gross_rate = r["gross_per_s"] * rate / r["orders_per_s"]
    stops = {"end of the runaway": float(seconds)}
    if "position" in controls:
        stops["position limit"] = controls["position"] / gross_rate
    if "capital" in controls:
        stops["capital threshold"] = controls["capital"] / gross_rate
    if "loss" in controls:
        mark = controls.get("mark_s", 1.0)
        stops["loss limit"] = math.ceil(controls["loss"] / loss_rate / mark) * mark
    if "collar_bp" in controls:
        stops["price collar"] = controls["collar_bp"] / 1e4 / r["drift_per_min"] * 60.0
    if "human_s" in controls:
        stops["kill switch (person)"] = controls["human_s"]
    who = min(stops, key=stops.get)
    t = min(stops[who], seconds)
    loss = loss_rate * t + flatten_cost * gross_rate * t
    return {"stopped_by": who, "seconds": t, "loss": loss, "gross": gross_rate * t, "orders": rate * t}


def normal_days(controls: dict, n: int = 2500, seed: int = 0) -> dict:
    """Ordinary days of a legitimate market-making book: peak message rate lognormal around 300 a second (log s.d.
    0.4), peak gross position around $150 million (0.35), worst intraday P&L normal with mean -$150,000 and s.d.
    $400,000, largest distance of a legitimate order from its reference lognormal around 30 bp (0.6). Returns the share
    of days on which each control would have fired."""
    rng = np.random.default_rng(seed)
    msgs = 300.0 * np.exp(0.4 * rng.standard_normal(n))
    gross = 150e6 * np.exp(0.35 * rng.standard_normal(n))
    worst = -150e3 + 400e3 * rng.standard_normal(n)
    dist = 30.0 * np.exp(0.6 * rng.standard_normal(n))
    out = {}
    if "throttle" in controls:
        out["throttle"] = float(np.mean(msgs > controls["throttle"]))
    if "position" in controls:
        out["position limit"] = float(np.mean(gross > controls["position"]))
    if "capital" in controls:
        out["capital threshold"] = float(np.mean(gross > controls["capital"]))
    if "loss" in controls:
        out["loss limit"] = float(np.mean(worst < -controls["loss"]))
    if "collar_bp" in controls:
        out["price collar"] = float(np.mean(dist > controls["collar_bp"]))
    return out
