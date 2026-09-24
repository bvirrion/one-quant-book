"""Chart data for Book 6, chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_rfr import cap_table, remaining_sd_profile  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "caplets.csv", "w") as f:
    f.write("i,label,back,fwd,share\n")
    for i, (s, e, _fw, b, fl, sh) in enumerate(cap_table()):
        f.write(f"{i},{s:.2f}-{e:.2f},{b / 1000:.3f},{fl / 1000:.3f},{sh:.3f}\n")
with open(OUT / "profile.csv", "w") as f:
    f.write("t,gfmm,meet\n")
    for t, g, mm in remaining_sd_profile():
        f.write(f"{t:.2f},{g:.3f},{mm:.3f}\n")

with open(OUT / "share.csv", "w") as f:
    f.write("s,hw,lin\n")
    for s_, _e, _fw, _b, _fl, sh in cap_table():
        lin = 100.0 * (0.25 / 3) / (s_ + 0.25 / 3)
        f.write(f"{s_:.2f},{sh:.3f},{lin:.3f}\n")
