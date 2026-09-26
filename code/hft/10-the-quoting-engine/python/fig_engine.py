"""Chart data for Book 11, chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_engine import compare  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "configs.csv", "w") as f:
    f.write("i,messages,fills,edge,median_age\n")
    for i, r in enumerate(compare().values()):
        f.write(f"{i},{r['messages_h']:.2f},{r['fills_h']:.2f},{r['edge_h']:.2f},{r['median_age']:.3f}\n")
