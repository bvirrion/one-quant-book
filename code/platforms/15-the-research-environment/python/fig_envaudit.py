"""Chart data for One Quant Book 15, chapter 15 (deterministic: the synthetic panel, seed 15)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_envaudit import EXCLUDED, panel  # noqa: E402
from research_lib import average_growth  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

df = panel()
with open(OUT / "choices.csv", "w") as f:
    f.write("case,by_country,by_country_year\n")
    cases = (("five excluded; all years", None, EXCLUDED), ("five excluded; from 1950", 1950, EXCLUDED),
             ("all countries; all years", None, ()), ("all countries; from 1950", 1950, ()))
    for label, since, excl in cases:
        a = average_growth(df, 90, since=since, exclude=excl)
        b = average_growth(df, 90, since=since, exclude=excl, weight="country-year")
        f.write(f"{label},{a:.2f},{b:.2f}\n")
