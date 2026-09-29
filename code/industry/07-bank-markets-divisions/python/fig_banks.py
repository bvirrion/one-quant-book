"""Chart data for Book 17, chapter 7 (deterministic, from the committed tables)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_banks as b  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

u = b.usd(2025)
with open(OUT / "mix2025.csv", "w") as f:
    f.write("k,bank,ficc_bn,equities_bn,equities_pct\n")
    for k, (bank, share) in enumerate(b.mix(2025)):
        f.write(f"{k},{bank},{u[bank][0] / 1000:.3f},{u[bank][1] / 1000:.3f},{100 * share:.1f}\n")
