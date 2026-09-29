"""Chart data for Book 17, chapter 6 (deterministic, from the committed FINRA tables)."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_firmsize as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

f = m.fit()
tail = [b for b in m.bins() if b.lo >= m.X_MIN]
n = sum(b.n for b in tail)
with open(OUT / "ccdf.csv", "w") as fh:
    fh.write("size,observed,pareto\n")
    above = n
    for b in tail:
        fh.write(f"{b.lo},{above / n:.5f},{((b.lo - 0.5) / (m.X_MIN - 0.5)) ** (-f['pareto']['alpha']):.5f}\n")
        above -= b.n

with open(OUT / "flows.csv", "w") as fh:
    fh.write("year,exit_pct,entry_pct\n")
    for r in m.entry_exit():
        fh.write(f"{r['year']},{100 * r['exit_rate']:.2f},{100 * r['entry_rate']:.2f}\n")
