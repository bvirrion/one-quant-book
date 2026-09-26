"""Chart data for Book 11, chapter 19 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_options as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "protection.csv", "w") as f:
    f.write("n,loss,lost\n")
    for n, r in h.protection_table().items():
        if n < 10**9:
            f.write(f"{n},{r['sweep_loss'] / 1000:.3f},{r['day_lost']}\n")
