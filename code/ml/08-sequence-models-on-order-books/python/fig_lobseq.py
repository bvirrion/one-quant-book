"""Chart data for Book 12, chapter 8 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_lobseq import scaling, table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

tb = table()
with open(OUT / "models.csv", "w") as f:
    f.write("i,model,ic,sd,acc\n")
    for i, (name, v) in enumerate(tb.items()):
        x = v.reshape(-1, 2)
        label = "logistic" if name.startswith("logistic") else name
        f.write(f"{i},{label},{x[:, 1].mean():.4f},{x[:, 1].std():.4f},{x[:, 0].mean():.4f}\n")
with open(OUT / "scaling.csv", "w") as f:
    f.write("sessions,tcn,logistic\n")
    for n in (4, 8, 16):
        a, b = scaling(n)
        f.write(f"{n},{a:.4f},{b:.4f}\n")
