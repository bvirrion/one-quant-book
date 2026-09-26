"""Chart data for Book 11, chapter 21 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_fx as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "hedge.csv", "w") as f:
    f.write("halflife,best,internalise,hedge\n")
    for s, r in h.hedging().items():
        if s > 0:
            f.write(f"{r['half_life']:.1f},{100 * r['best']:.0f},"
                    f"{r['internalise_all'] / 10:.2f},{r['hedge_all'] / 10:.2f}\n")
