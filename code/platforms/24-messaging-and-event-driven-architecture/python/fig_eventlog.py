"""Chart data for One Quant Book 15, chapter 24 (deterministic: fills seed 24, 100 crash schedules per mode)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_eventlog import MODES, publishing, schedules  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

runs = {m: schedules(m) for m in MODES}
with open(OUT / "modes.csv", "w") as f:
    f.write("mode,crashes,lost,duplicated,lost_per_1000,dup_per_1000,max_error,median_error\n")
    for m, r in runs.items():
        f.write(f"{m},{r['crashes']},{r['lost']},{r['dup']},{r['lost_per_1000']:.0f},{r['dup_per_1000']:.0f},"
                f"{r['max_error']},{np.median(r['worst']):.0f}\n")
with open(OUT / "worst.csv", "w") as f:
    f.write("rank,at_most_once,at_least_once,atomic\n")
    cols = [sorted(runs[m]["worst"]) for m in MODES]
    for i, row in enumerate(zip(*cols, strict=True)):
        f.write(f"{i + 1},{row[0]},{row[1]},{row[2]}\n")
with open(OUT / "outbox.csv", "w") as f:
    f.write("design,lost,phantom,duplicated\n")
    for d in ("write-then-publish", "publish-then-write", "outbox-no-idempotence", "outbox"):
        r = publishing(d)
        f.write(f"{d},{r['lost']},{r['phantom']},{r['duplicated']}\n")
