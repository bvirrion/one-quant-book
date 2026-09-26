"""Chart data for Book 10, chapter 18 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_sor import JITTERS, VENUES, race, sweep_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "race.csv", "w") as f:
    f.write("i,venue,spray,cancel,sync\n")
    for i, (name, spray, cancel, sync) in enumerate(race()):
        f.write(f"{len(VENUES) - i},{name},{spray},{cancel if cancel is not None else 'nan'},{sync}\n")
s = sweep_study()
with open(OUT / "jitter.csv", "w") as f:
    f.write("jitter,spray,sync,spray_full,sync_full\n")
    for j in JITTERS:
        f.write(f"{j},{100 * s[(j, False)]['ratio']:.2f},{100 * s[(j, True)]['ratio']:.2f},"
                f"{100 * s[(j, False)]['full']:.1f},{100 * s[(j, True)]['full']:.1f}\n")
