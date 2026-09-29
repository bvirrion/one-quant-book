"""Chart data for Book 17, chapter 26."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_hours as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
h = a.heat()
with open(OUT / "heat.csv", "w") as f:
    f.write("hour,day,open\n")
    for d in range(7):
        for hr in range(24):
            f.write(f"{hr},{d},{h[d][hr]:.3f}\n")
s = a.staffing()
rows = (("futures; no leave", a.fw.headcount(s["futures_shift_hours"], a.PER_SHIFT, leave_weeks=0.0)),
        ("futures", s["futures_people"]), ("futures and crypto; no leave", s["continuous_people_no_leave"]),
        ("futures and crypto", s["continuous_people"]))
with open(OUT / "people.csv", "w") as f:
    f.write("pos,book,people,label\n")
    for i, (lab, v) in enumerate(rows):
        f.write(f"{i + 1},{lab},{v:.3f},{v:.2f}\n")
