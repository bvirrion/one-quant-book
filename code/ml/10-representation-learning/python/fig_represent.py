"""Chart data for Book 12, chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_represent import compare  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

KEYS = ["raw ridge", "from scratch", "autoencoder probe", "contrastive probe", "predictive probe",
        "predictive fine-tuned", "features ridge"]
with open(OUT / "labels.csv", "w") as f:
    f.write("windows," + ",".join(k.replace(" ", "_").replace("-", "_") for k in KEYS) + "\n")
    for n, label in ((300, 300), (1000, 1000), (0, 4444)):
        c = compare(n)
        f.write(f"{label}," + ",".join(f"{c[k]:.4f}" for k in KEYS) + "\n")
