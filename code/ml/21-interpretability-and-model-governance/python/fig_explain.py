"""Chart data for Book 12, chapter 21: partial dependence and ALE against the truth; ICE curves."""
import pathlib

import ml_explain as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "21-interpretability-and-model-governance"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g, pd, edges, a = m.curves("correlation 0.99")
    _, X, _ = m.model("correlation 0.99")
    shift = X[:, 0].mean()
    with open(OUT / "pdale.csv", "w") as f:
        f.write("x,pd,truth\n")
        for x, v in zip(g, pd, strict=True):
            f.write(f"{x:.3f},{v:.4f},{x - shift:.4f}\n")
    with open(OUT / "ale.csv", "w") as f:
        f.write("x,ale\n")
        for x, v in zip(edges, a, strict=True):
            f.write(f"{x:.4f},{v:.4f}\n")
    C, pd_slope, _, _ = m.ice_x3()
    with open(OUT / "ice.csv", "w") as f:
        f.write("x," + ",".join(f"c{i}" for i in range(len(C))) + ",pd\n")
        pd = C.mean(0)
        for k, x in enumerate(m.GRID):
            f.write(f"{x:.3f}," + ",".join(f"{v:.4f}" for v in C[:, k]) + f",{pd[k]:.4f}\n")


if __name__ == "__main__":
    main()
