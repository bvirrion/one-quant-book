"""Chart data for Book 12, chapter 16: autocorrelation of absolute returns by lag; TSTR and TSTS Sharpe ratios."""
import pathlib

import ml_gen as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "16-generative-models-and-synthetic-data"
COLS = {"real": "real", "block bootstrap": "boot", "GARCH-t": "garch", "VAE": "vae", "GAN": "gan", "diffusion": "diff"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    D, gens = m.data(), m.generators()
    acf = {"real": m.abs_acf(D["train"])} | {k: m.abs_acf(f(4000, 1)) for k, f in gens.items()}
    with open(OUT / "absacf.csv", "w") as f:
        f.write("lag," + ",".join(COLS.values()) + "\n")
        for i in range(20):
            f.write(f"{i + 1}," + ",".join(f"{acf[k][i]:.4f}" for k in COLS) + "\n")
    j = m.judge()
    with open(OUT / "sharpe.csv", "w") as f:
        f.write("i,name,tsts,tstr\n")
        for i, k in enumerate(m.NAMES):
            f.write(f"{i},{COLS[k]},{j[k]['tsts'][1]:.2f},{j[k]['tstr'][1]:.2f}\n")
    with open(OUT / "trtr.csv", "w") as f:
        f.write(f"x,y\n-0.5,{j['real']['tstr'][1]:.2f}\n4.5,{j['real']['tstr'][1]:.2f}\n")


if __name__ == "__main__":
    main()
