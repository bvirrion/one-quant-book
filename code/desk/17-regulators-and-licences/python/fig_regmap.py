"""Chart data for Book 16, chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_regmap as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "periods.csv", "w") as f:
    f.write("pos,label,days\n")
    for i, (k, d) in enumerate(m.PERIODS):
        f.write(f"{i},{k.replace(',', ';')},{d}\n")

with open(OUT / "profiles.csv", "w") as f:
    f.write("pos,profile,required,obligation,check\n")
    for i, (k, v) in enumerate(m.profiles().items()):
        b = v["by_status"]
        f.write(f"{i},{k.replace(',', ';')},{b['required']},{b['obligation']},{b['check']}\n")
