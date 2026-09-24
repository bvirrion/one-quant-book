"""Chart data for Book 6, chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_cms import cms_table, replication_contributions, steepener  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "cmsadj.csv", "w") as f:
    f.write("e,fwd,flat,smile\n")
    for e, fw, a, b in cms_table():
        f.write(f"{e:.0f},{fw:.4f},{a:.3f},{b:.3f}\n")

with open(OUT / "contrib.csv", "w") as f:
    f.write("k,c\n")
    for k, c in replication_contributions():
        f.write(f"{k:.2f},{c:.5f}\n")

with open(OUT / "steep.csv", "w") as f:
    f.write("rho,p\n")
    for i in range(0, 13):
        rho = 0.50 + 0.04 * i
        f.write(f"{rho:.2f},{steepener(rho)['participation']:.4f}\n")
