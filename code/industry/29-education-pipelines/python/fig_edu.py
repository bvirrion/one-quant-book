"""Chart data for Book 17, chapter 29."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_edu as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
c = a.completions()
with open(OUT / "masters.csv", "w") as f:
    f.write("year," + ",".join(x.replace(" ", "_") for x in a.FIELDS) + "\n")
    for y in (2010, 2014, 2019, 2024):
        vals = [c[(y, fld, "master")] for fld in a.FIELDS]
        f.write(f"{y}," + ",".join("nan" if v == 0 else str(v) for v in vals) + "\n")
with open(OUT / "levels.csv", "w") as f:
    f.write("pos,field,bachelor,master,doctorate\n")
    for i, fld in enumerate(reversed(a.FIELDS)):
        b, m, d = (c[(2024, fld, lv)] for lv in ("bachelor", "master", "doctorate (research)"))
        f.write(f"{i + 1},{fld},{b},{m},{d}\n")
