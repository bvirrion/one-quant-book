"""Chart data for Book 12, chapter 15: nowcast error by quarter (raw and raked); information coefficient by period."""
import pathlib

import ml_altdata as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "15-alternative-data-pipelines"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw, raked = m.errors("raw"), m.errors("raked")
    with open(OUT / "errors.csv", "w") as f:
        f.write("quarter,raw,raked\n")
        for q in range(4, m.Q):
            f.write(f"{q},{raw[q]:.2f},{raked[q]:.2f}\n")
    with open(OUT / "events.csv", "w") as f:
        f.write("quarter,label\n")
        f.write(f"{m.LAUNCH},launch\n{m.CHANGE},partner\n")
    ic = m.ic_summary()
    with open(OUT / "ic.csv", "w") as f:
        f.write("i,period,raw,raked\n")
        for i, p in enumerate(("backfilled", "live before the change", "live after the change")):
            f.write(f"{i},{p.replace(' ', '')},{ic['raw'][p]:.3f},{ic['raked'][p]:.3f}\n")


if __name__ == "__main__":
    main()
