"""Chart data for Book 11, chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_optarb as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "dividend.csv", "w") as f:
    f.write("fail,per_public,captured\n")
    for fl, r in h.dividend().items():
        f.write(f"{100 * fl:g},{r['per_public']:.4f},{100 * r['captured']:.2f}\n")
