"""Chart data for One Quant Book 15, chapter 4 (deterministic: the simulated week through the store)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_tickstore import DATES, GEN, build  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

info = build(GEN / "store_week")
with open(OUT / "sizes.csv", "w") as f:
    f.write("k,day,events,flat,ipc,parquet\n")
    for k, d in enumerate(DATES):
        i = info[k]
        pq = sum(v["bytes"] for v in i["compacted"].values()) / 1e6 if "compacted" in i else 0.0
        f.write(f"{k},{d[5:]},{i['events']},{i['flat_bytes'] / 1e6:.4f},{i['ipc_bytes'] / 1e6:.4f},{pq:.4f}\n")
