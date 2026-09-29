"""Chart data for Book 16, chapter 5 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_bank as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

j = m.jpm()
with open(OUT / "stack.csv", "w") as f:
    f.write("k,label,minimum,buffer,gsib,actual\n")
    f.write(f"0,CET1 / RWA,4.5,{j['scb_pct']:.1f},{j['gsib_method2_pct']:.1f},{j['cet1_ratio_pct']:.1f}\n")
    f.write(f"1,Tier 1 / leverage exposure,3.0,{j['slr_requirement_pct'] - 3.0:.1f},0.0,{j['slr_pct']:.1f}\n")

t, _ = m.roae_table()
with open(OUT / "roae.csv", "w") as f:
    f.write("k,desk,rwa,leverage,binding\n")
    for i, d in enumerate(m.DESKS):
        f.write(f"{i},{d.name},{100 * t['rwa'][i]:.1f},{100 * t['leverage'][i]:.1f},{100 * t['binding'][i]:.1f}\n")

x = m.mix()
with open(OUT / "mix.csv", "w") as f:
    f.write("k,desk,today,optimal\n")
    for i, d in enumerate(m.DESKS):
        f.write(f"{i},{d.name},1.0,{x[i]:.3f}\n")
