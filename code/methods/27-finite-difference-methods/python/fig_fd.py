"""Chart data for Book 4, chapter 27 (finite-difference methods): figdata/methods/27-finite-difference-methods/."""
import pathlib

from qm_fd import amplification_curves, bs_gamma, convergence, digital_placement, sawtooth

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "methods" / "27-finite-difference-methods"
OUT.mkdir(parents=True, exist_ok=True)

c = amplification_curves()
with open(OUT / "amplification.csv", "w") as f:
    f.write("xi,explicit049,explicit051,implicit,cn\n")
    for i, xi in enumerate(c["xi"]):
        f.write(f"{xi:.5f},{c['explicit_049'][i]:.5f},{c['explicit_051'][i]:.5f},{c['implicit'][i]:.5f},{c['cn'][i]:.5f}\n")

s = sawtooth(rannacher=(0, 4))
with open(OUT / "sawtooth.csv", "w") as f:
    f.write("S,exact,cn,cn4\n")
    for i, S in enumerate(s[0]["S"]):
        f.write(f"{S:.4f},{bs_gamma(S):.6f},{s[0]['gamma'][i]:.6f},{s[4]['gamma'][i]:.6f}\n")

conv = convergence()
with open(OUT / "convergence.csv", "w") as f:
    f.write("n,implicit,cn,cn2,cn4\n")
    for k in range(len(conv["cn"])):
        errs = ",".join(f"{conv[s][k][2]:.4e}" for s in ("implicit", "cn", "cn+2", "cn+4"))
        f.write(f"{conv['cn'][k][0]},{errs}\n")

with open(OUT / "digital.csv", "w") as f:
    f.write("n,node,midcell\n")
    for n, a, b in digital_placement():
        f.write(f"{n},{a:.4e},{b:.4e}\n")
