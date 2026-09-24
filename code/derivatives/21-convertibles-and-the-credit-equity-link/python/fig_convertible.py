"""Chart data for Book 5, Chapter 21 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_convertible import CB, LAM0, S0, P, profile, stress_grid

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

e2c, const = profile(P), profile(0.0)
with open(OUT / "profile.csv", "w") as f:
    f.write("s,cb,cb_const,floor,floor_const,conv,delta,delta_const,gamma,gamma_const,hazard\n")
    for i, s in enumerate(e2c["s"]):
        hz = 100 * min(LAM0 * (s / S0) ** (-P), 2.0)
        f.write(f"{s:.2f},{e2c['cb'][i]:.4f},{const['cb'][i]:.4f},{e2c['floor'][i]:.4f},{const['floor'][i]:.4f},"
                f"{CB.ratio * s:.4f},{e2c['delta'][i]:.5f},{const['delta'][i]:.5f},{e2c['gamma'][i]:.5f},"
                f"{const['gamma'][i]:.5f},{hz:.3f}\n")

moves = (-0.3, -0.2, -0.1, 0.0, 0.1, 0.2)
sg = stress_grid(moves)
with open(OUT / "stress.csv", "w") as f:
    f.write("move,w0,w150,w300\n")
    for i, m in enumerate(moves):
        f.write(f"{100 * m:.0f},{sg[0.0][i]:.4f},{sg[150.0][i]:.4f},{sg[300.0][i]:.4f}\n")
