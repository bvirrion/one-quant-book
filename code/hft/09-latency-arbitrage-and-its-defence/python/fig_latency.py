"""Chart data for Book 11, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_latency import by_lp_latency, defence  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "sniped.csv", "w") as f:
    f.write("lp_median,continuous,asymmetric\n")
    for m, r in by_lp_latency().items():
        f.write(f"{m:g},{r['continuous']:.4f},{r['asymmetric']:.4f}\n")

with open(OUT / "defence.csv", "w") as f:
    f.write("delay_ms,informed,markout\n")
    for d, r in defence().items():
        if d is not None:
            f.write(f"{1000 * d:g},{100 * r['informed']:.1f},{r['markout']:.3f}\n")
