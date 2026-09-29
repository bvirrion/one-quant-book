"""Chart data for One Quant Book 15, chapter 3 (deterministic: synthetic quotes, pyarrow's reads counted)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_colfmt import QUERIES, ROW_GROUPS, study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = study()
LAYOUTS = ("shuffled", "time order", "symbol, then time")
with open(OUT / "rowgroups.csv", "w") as f:
    f.write("rows,shuffled,time,symbol\n")
    for rg in ROW_GROUPS:
        f.write(f"{rg}," + ",".join(f"{s[(lay, rg, 'one symbol, one hour')][1] / 1e6:.4f}" for lay in LAYOUTS) + "\n")
with open(OUT / "queries.csv", "w") as f:
    f.write("k,query,shuffled,time,symbol\n")
    for k, q in enumerate(QUERIES):
        f.write(f"{k},{q.replace(',', ';')}," + ",".join(
            f"{100 * s[(lay, 32_768, q)][1] / s[(lay, 32_768, q)][0]:.3f}" for lay in LAYOUTS) + "\n")
