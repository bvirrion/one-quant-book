"""Chart data for One Quant Book 15, chapter 11 (deterministic: twenty one-hour firm.tape sessions, seeds 1-20)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_btengine import ladder, summary  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rows = ladder()
s = summary(rows)
with open(OUT / "ladder.csv", "w") as f:
    f.write("level,label,pnl,se,fills\n")
    for lv, lab in ((2, "level 2 bars"), (3, "level 3 replay"), (4, "level 4 reactive")):
        f.write(f"{lv},{lab},{s[f'pnl{lv}'][0]:.2f},{s[f'pnl{lv}'][1]:.2f},{s[f'fills{lv}'][0]:.1f}\n")
with open(OUT / "sessions.csv", "w") as f:
    f.write("seed,pnl3,pnl4\n")
    for r in rows:
        f.write(f"{r['seed']},{r['pnl3']:.2f},{r['pnl4']:.2f}\n")
with open(OUT / "decomposition.csv", "w") as f:
    n3, n4 = s["fills3"][0], s["fills4"][0]
    f.write("part,replay,reactive,n_replay,n_reactive\n")
    f.write(f"shared fills,{s['shared3'][0]:.2f},{s['shared4'][0]:.2f},"
            f"{n3 - s['n_only3'][0]:.1f},{n4 - s['n_only4'][0]:.1f}\n")
    f.write(f"replay-only fills,{s['only3'][0]:.2f},0,{s['n_only3'][0]:.1f},0\n")
    f.write(f"reactive-only fills,0,{s['only4'][0]:.2f},0,{s['n_only4'][0]:.1f}\n")
with open(OUT / "divergence.csv", "w") as f:
    f.write("seed,first_fill_index,first_time\n")
    for r in rows:
        f.write(f"{r['seed']},{r['first_div']},{r['first_div_t']:.2f}\n")
