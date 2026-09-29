"""Chart data for Book 16, chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_limits as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

a = m.allocation()
va = m.value_added()
with open(OUT / "capital.csv", "w") as f:
    f.write("k,name,standalone,euler,incremental,va_standalone,va_euler\n")
    for i, nm in enumerate(m.NAMES):
        f.write(f"{i},{nm},{a['standalone'][i]:.1f},{a['euler'][i]:.1f},{a['incremental'][i]:.1f},"
                f"{va['standalone'][i]:.2f},{va['euler'][i]:.2f}\n")

t, v, hard = m.var_path()
with open(OUT / "varpath.csv", "w") as f:
    f.write("day,var,soft,hard\n")
    for d, x, h in zip(t, v, hard, strict=True):
        f.write(f"{d},{x:.3f},6.0,{h:.1f}\n")
