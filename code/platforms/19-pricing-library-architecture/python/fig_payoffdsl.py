"""Chart data for One Quant Book 15, chapter 19 (deterministic: 100,000 paths on common random numbers)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_payoffdsl import validation  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "validation.csv", "w") as f:
    f.write("product,script,se,library,diff_se,engine\n")
    for r in validation():
        lib = "" if r["library"] != r["library"] else f"{r['library']:.4f}"
        d = "" if r["diff_se"] != r["diff_se"] else f"{r['diff_se']:.2f}"
        f.write(f"{r['product'].replace(',', ';')},{r['script']:.4f},{r['se']:.4f},{lib},{d},{r['engine']}\n")
