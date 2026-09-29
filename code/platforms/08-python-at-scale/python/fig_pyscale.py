"""Chart data for One Quant Book 15, chapter 8 (deterministic: bytes of one column in four representations)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_pyscale import symbol_memory  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "memory.csv", "w") as f:
    f.write("k,representation,mb\n")
    for k, (name, b) in enumerate(symbol_memory().items()):
        f.write(f"{k},{name},{b / 1e6:.3f}\n")
