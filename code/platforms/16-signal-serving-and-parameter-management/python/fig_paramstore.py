"""Chart data for One Quant Book 15, chapter 16 (deterministic: ten one-hour firm.tape sessions, seeds 1-10, on
firm.exchsim, with and without the units error)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_paramstore import T0, incident  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = incident()
with open(OUT / "timeline.csv", "w") as f:
    f.write("minutes,all_k,staged_k\n")
    for t, a, s in zip(r["grid"], r["all"]["path"], r["staged"]["path"], strict=True):
        if t >= T0 - 60 and t <= T0 + 1200:
            f.write(f"{(t - T0) / 60:.3f},{a / 1e3:.1f},{s / 1e3:.1f}\n")
with open(OUT / "summary.csv", "w") as f:
    f.write("policy,detect_min,peak_k,dollar_min_k\n")
    for k, lab in (("all", "all at once"), ("staged", "staged rollout"), ("schema", "schema check")):
        x = r[k]
        f.write(f"{lab},{x['detect_min']:.1f},{x['peak'] / 1e3:.1f},{x['dollar_min'] / 1e3:.1f}\n")
with open(OUT / "detection.csv", "w") as f:
    f.write("strategy,detect_min\n")
    for s, d in r["detection"].items():
        f.write(f"q{s:02d},{'' if d is None else f'{(d - T0) / 60:.0f}'}\n")
