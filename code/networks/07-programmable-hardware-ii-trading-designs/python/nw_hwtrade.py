"""Chapter 7 of One Quant Book 14: a hardware trigger on the simulator's feed, and its place in a hybrid system.

    run(thresh, max_qty, kill_at)     the design's orders on the chapter's fixture (Python cycle model of firm.hwtrade)
    decision_cycles()                 per order: cycles from its packet's first beat, cycles left in the packet
    paths()                           wire-to-wire of the software path (chapter 5) and of the hardware path
    win_probability(path, median_ns, sigma, n, seed)    against one competitor with a lognormal latency (model)
    burst_before_kill(react_us, clock_mhz, burst, refill)   orders the token bucket can let out before software acts
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("hwtrade", "wirepath", "latbudget"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
sys.path.insert(0, str(ROOT / "code" / "networks" / "05-capturing-and-monitoring-the-network" / "python"))
import firm_hwtrade as hw  # noqa: E402
import firm_wirepath as wp  # noqa: E402
import make_hwtrade_fixture as mf  # noqa: E402
import nw_capture  # noqa: E402

CLOCK_MHZ = 156.25
CARD_HW = dict(rx=120.0, tx=120.0)       # ns through the card's transceiver and MAC each way: model values
THRESH, MAXQ = 1_000_200, 10_000


def fixture():
    pk = mf.load()
    return pk, hw.beats_of(pk)


def run(thresh=THRESH, max_qty=MAXQ, kill_at=-1):
    return hw.CycleModel().run(fixture()[1], thresh, max_qty, kill_at)


def decision_cycles(thresh=THRESH):
    pk, beats = fixture()
    starts, ends, c = [], [], 0
    for p in pk:
        n = len(hw.hk.beats(p))
        starts.append(c)
        ends.append(c + n - 1)
        c += n + 2
    starts, ends = np.array(starts), np.array(ends)
    out = []
    for cycle, *_ in run(thresh)[0]:
        beat = cycle - 2                                          # the beat that completed the triggering message
        k = int(np.searchsorted(starts, beat, side="right") - 1)
        out.append((cycle - starts[k] + 1, ends[k] - beat))      # from the first beat; beats still to come
    return np.array(out)


def paths(n=100_000, seed=1):
    soft = nw_capture.stages()
    wire = [s for s in soft if s.kind == "wire"]
    card = [wp.Stage("card in (transceiver, MAC)", CARD_HW["rx"], 0, "card"),
            wp.Stage("card out (transceiver, MAC)", CARD_HW["tx"], 0, "card")]
    hard = wire[:1] + card[:1] + [hw.wirepath_stage(3, CLOCK_MHZ)] + card[1:] + wire[1:]
    return {"software": wp.compose(soft, n, seed)["total"], "hardware": wp.compose(hard, n, seed)["total"],
            "hardware_stages": hard, "software_stages": soft}


def win_probability(total_ns, median_ns, sigma=0.3, seed=2):
    rng = np.random.default_rng(seed)
    comp = median_ns * np.exp(sigma * rng.standard_normal(len(total_ns)))
    return float(np.mean(total_ns < comp))


def burst_before_kill(react_us, clock_mhz=CLOCK_MHZ, burst=4, refill=64):
    return burst + int(react_us * clock_mhz // refill)
