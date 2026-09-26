"""Chart data for Book 11, chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_wholesale as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "pi.csv", "w") as f:
    f.write("pi,retail,inst,improvement\n")
    for p, r in h.by_pi().items():
        f.write(f"{100 * p:g},{r['retail']['net_ex_inventory']:.4f},{r['inst']['net_ex_inventory']:.4f},"
                f"{h.fw.rule605(h.retail(), p)['improvement']:.4f}\n")

with open(OUT / "limits.csv", "w") as f:
    f.write("limit,mean,sd,hedge\n")
    for lim, r in h.limits().items():
        f.write(f"{lim / 1000:g},{r['mean']:.4f},{r['sd']:.4f},{r['hedge']:.4f}\n")
