"""Chart data for Book 11, chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_sports as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "delay.csv", "w") as f:
    f.write("delay,loss,sniped\n")
    for d, r in h.by_delay().items():
        f.write(f"{d:g},{r['loss_per_goal']:.3f},{100 * r['sniped_share']:.2f}\n")

path, goals = h.match_path()
with open(OUT / "match.csv", "w") as f:
    f.write("minute,p\n")
    for m, p in path:
        f.write(f"{m},{p:.4f}\n")
