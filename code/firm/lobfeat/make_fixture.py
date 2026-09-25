"""Writes the shared fixture of firm.lobfeat: the first 3,000 messages of a seeded firm.tape session, an illustrative
microprice table of ten buckets, and the Python reference's features after every message. Run from the repository
root: .venv/bin/python code/firm/lobfeat/make_fixture.py"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_lobfeat import FIELDS, run  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

msgs = simulate(TapeConfig(seconds=120.0, news_at=None, seed=21)).msgs[:3000]
g = np.linspace(-0.3, 0.3, 10)
out = run(msgs, 5, g)
d = HERE / "data"
d.mkdir(exist_ok=True)
with open(d / "fixture_g.csv", "w") as f:
    f.write("bucket,g\n")
    for i, x in enumerate(g):
        f.write(f"{i},{float(x)!r}\n")
with open(d / "fixture_msgs.csv", "w") as f:
    f.write("kind,oid,side,price,qty\n")
    for m in msgs:
        f.write(f"{m['kind'].decode()},{m['oid']},{m['side']},{m['price']},{m['qty']}\n")
with open(d / "fixture_expected.csv", "w") as f:
    f.write(",".join(FIELDS) + "\n")
    for i in range(len(msgs)):
        if np.isnan(out["bid"][i]):
            f.write(",".join(["nan"] * len(FIELDS)) + "\n")
            continue
        vals = []
        for k in FIELDS:
            v = out[k][i]
            vals.append(str(int(v)) if k in ("bid", "ask", "bid_qty", "ask_qty", "ofi", "ofi_cum") else repr(float(v)))
        f.write(",".join(vals) + "\n")
print(len(msgs), "messages")
