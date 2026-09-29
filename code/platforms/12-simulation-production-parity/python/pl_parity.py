"""Simulation-production parity (One Quant Book 15, chapter 12).

One quoting strategy (a lot at the touch, one tick wider during a thirty-second opening period that a timer ends,
an inventory limit of three lots) is hosted by firm.strathost in three environments on the same firm.tape session:
the simulator in process, a production-shaped path through Book 13's gateway and an encoded byte stream, and the
replay of the production run's input journal. Four parity defects are planted one at a time; the harness reports,
for each, the first diverging output, the inputs delivered before it and the outputs affected in the hour. With
every defect fixed, the three environments agree on every output for ten sessions.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/strathost"))
import firm_strathost as S  # noqa: E402

SEC = 10**9
TICK = 100                                            # 0.01 in 1/10,000
OPENING = 30 * SEC
REPLAY_MACHINE = (72_000 * SEC, 100.0)                # a replay at 20:00, a hundred times faster than the session
DEFECTS = ("wall_clock", "float_prices", "arrival_order", "acked_working")


class OpeningQuoter(S.HostedStrategy):
    """A lot at the touch, a tick wider until the opening ends; stop adding at three lots."""

    def __init__(self, wall_clock: bool = False, limit: int = 300):
        self.wall, self.limit, self.mine = wall_clock, limit, {}

    def _now(self, ctx) -> int:
        return S.machine_ns() if self.wall else ctx.now   # the defect reads the machine

    def on_start(self, ctx):
        self.open_end = self._now(ctx) + OPENING
        ctx.set_timer(self.open_end - ctx.now, 1)        # mixes clocks under the defect

    def on_timer(self, ctx, tag):
        for oid in list(self.mine):                       # opening over: requote at the touch
            ctx.cancel(oid)
        self.mine = {}

    def on_book(self, ctx, top):
        bid, _, ask, _ = top
        tick = TICK / S.SCALE if isinstance(bid, float) else TICK
        wide = self._now(ctx) < self.open_end
        want = {1: bid - tick if wide else bid, -1: ask + tick if wide else ask}
        live = set(ctx.working())
        self.mine = {o: sp for o, sp in self.mine.items() if o in live}
        have = set()
        for oid, (side, px) in list(self.mine.items()):
            if px != want[side]:
                ctx.cancel(oid)
                del self.mine[oid]
            else:
                have.add(side)
        for side in (1, -1):
            if side not in have and side * ctx.position < self.limit:
                self.mine[ctx.send(side, want[side], 100)] = (side, want[side])


def run_three(seed: int, defects: S.Defects, seconds: float = 3600.0) -> dict:
    """Production-shaped run, in-process simulator run and replay of the production journal."""
    wall = defects.wall_clock
    prod = S.run_env("prod", OpeningQuoter(wall), seconds, seed, defects, machine=(None, 1.0))
    sim = S.run_env("sim", OpeningQuoter(wall), seconds, seed, S.FIXED, machine=REPLAY_MACHINE)
    rep = S.replay(prod.journal, OpeningQuoter(wall), S.FIXED, prod.start, machine=REPLAY_MACHINE)
    return {"prod": prod, "sim": sim, "replay": rep,
            "vs_sim": S.compare(prod, sim), "vs_replay": S.compare(prod, rep)}


def defect_table(seed: int = 1, seconds: float = 3600.0) -> list[dict]:
    rows = []
    for name in DEFECTS:
        r = run_three(seed, S.Defects(**{name: True}), seconds)
        for against in ("vs_sim", "vs_replay"):
            p = r[against]
            rows.append({"defect": name, "against": against[3:], "same": p.same, "first": p.first,
                         "events": p.events_before, "t": (p.t_first - r["prod"].start) / SEC if p.t_first >= 0 else -1,
                         "affected": p.affected, "outputs": len(r["prod"].outputs)})
    return rows


def clean(seeds=range(1, 11), seconds: float = 3600.0) -> list[dict]:
    out = []
    for s in seeds:
        r = run_three(s, S.FIXED, seconds)
        out.append({"seed": s, "outputs": len(r["prod"].outputs), "inputs": len(r["prod"].inputs),
                    "same_sim": r["vs_sim"].same, "same_replay": r["vs_replay"].same})
    return out
