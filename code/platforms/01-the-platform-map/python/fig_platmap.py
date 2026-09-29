"""Chart data for One Quant Book 15, chapter 1 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_platmap import HOOK_NIGHT, firm, jobs  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

m = firm()
sched, chain = m.schedule(), set(m.longest_chain())
order = [j.name for j in jobs()]
with open(OUT / "gantt_nominal.csv", "w") as f:
    f.write("k,job,start,other,chain\n")
    for k, name in enumerate(reversed(order)):
        s, e = sched[name]
        d = (e - s) / 60
        f.write(f"{k},{name},{s / 60:.4f},{0 if name in chain else d:.4f},{d if name in chain else 0:.4f}\n")

fixed = firm(risk_start=300)
hs, ready = fixed.schedule(HOOK_NIGHT), fixed.ready_times(HOOK_NIGHT)
rows = [("golden copy", "golden copy"), ("positions", "positions"), ("pnl", "pnl"),
        ("risk batch (fixed 21:00)", "risk batch")]
with open(OUT / "gantt_hook.csv", "w") as f:
    f.write("k,job,start,dur\n")
    for k, (lab, name) in enumerate(reversed(rows)):
        s, e = hs[name]
        f.write(f"{k},{lab},{s / 60:.4f},{(e - s) / 60:.4f}\n")
with open(OUT / "hook_ready.csv", "w") as f:
    f.write("dataset,ready\n")
    for d in ("security master", "positions"):
        f.write(f"{d},{ready[d] / 60:.4f}\n")

blast = m.blast_radius()
with open(OUT / "blast.csv", "w") as f:
    f.write("k,input,datasets\n")
    for k, (name, n) in enumerate(sorted(blast.items(), key=lambda x: (x[1], x[0]))):
        f.write(f"{k},{name},{n}\n")
