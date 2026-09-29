"""Chart data for Book 17, chapter 25."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_leader as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
s = a.summary(a.run())
with open(OUT / "partner.csv", "w") as f:
    f.write("year,draw,capital,cap_p05\n")
    for t in range(a.YEARS):
        f.write(f"{t + 1},{s['by_year_draw'][t]:.3f},{s['by_year_cap'][t]:.3f},{s['by_year_cap_p05'][t]:.3f}\n")
with open(OUT / "smf.csv", "w") as f:
    f.write("pos,tier,count\n")
    for i, tier in enumerate(("limited scope", "core", "enhanced")):
        f.write(f"{i + 1},{tier},{a.fr.smf_count(tier)}\n")
sv = a.survey()
LAB = (("11-1021", "general and operations managers"), ("11-3021", "computer and information systems managers"),
       ("11-3031", "financial managers"), ("11-1011", "chief executives"))
with open(OUT / "survey.csv", "w") as f:
    f.write("pos,label,p10,p25,p50,p75,p90\n")
    for i, (occ, lab) in enumerate(LAB):
        vals = ",".join(f"{float(sv[occ][q]) / 1000:.1f}" for q in ("p10", "p25", "p50", "p75", "p90"))
        f.write(f"{i + 1},{lab},{vals}\n")
