"""Chart data for One Quant Book 15, chapter 28 (deterministic: quiet days seeds 1-30, incident day seed 999)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_observe import (  # noqa: E402
    BURN_RULES,
    FRESH,
    INCIDENTS,
    TARGET,
    O,
    budget,
    clock,
    compare,
    incident,
    quiet_day,
    stall_timeline,
    traced,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)


def fmt(x):
    return "none" if x is None else f"{x:.0f}"


with open(OUT / "rules.csv", "w") as f:
    f.write("rule,feed_stall_s,intermittent_s,slow_consumer_s,false_pages_month\n")
    for r in compare():
        f.write(f"{r['rule']},{fmt(r['feed stall'])},{fmt(r['intermittent stalls'])},{fmt(r['slow consumer'])},"
                f"{r['false_pages']:.0f}\n")
with open(OUT / "budget.csv", "w") as f:
    b = budget()
    f.write("bad_seconds,budget_seconds,used_pct,pauses_over_5s\n")
    f.write(f"{b['bad_seconds']},{b['budget_seconds']:.0f},{100 * b['used']:.1f},{b['pauses_over_5s']}\n")
with open(OUT / "quiet.csv", "w") as f:
    q = quiet_day(13)
    f.write("minute,max_age\n")
    for m in range(len(q) // 60):
        f.write(f"{m},{q[60 * m:60 * m + 60].max():.3f}\n")
for kind, name in (("slow consumer", "slow"), ("intermittent stalls", "intermittent")):
    age = incident(kind)
    start, length = INCIDENTS[kind]
    bad = (age > FRESH).astype(float)
    lim = 1 - TARGET
    long_s, short_s = BURN_RULES[0][0], BURN_RULES[0][1]
    lw, sw = O._window_share(bad, long_s) / lim, O._window_share(bad, short_s) / lim
    with open(OUT / f"incident_{name}.csv", "w") as f:
        f.write("t_min,age,burn_1h,burn_5m\n")
        for t in range(start - 300, start + min(length, 1500), 5):
            f.write(f"{(t - start) / 60:.3f},{age[t]:.3f},{lw[t]:.2f},{sw[t]:.2f}\n")
for case, lag in (("normal", 0.05), ("slow", 60.0)):
    with open(OUT / f"trace_{case}.csv", "w") as f:
        f.write("span,start_ms,dur_ms,row\n")
        for i, s in enumerate(traced(100.0, lag)[1:]):
            name = s.name.replace(":", "")
            f.write(f"{name},{1e3 * (s.start - 100.0):.3f},{1e3 * (s.end - s.start):.3f},{i}\n")
with open(OUT / "timeline.csv", "w") as f:
    f.write("clock,source,event\n")
    for t, src, text in stall_timeline():
        f.write(f"{clock(t)},{src},{text.replace(',', ';')}\n")
assert np.isfinite(budget()["used"])
