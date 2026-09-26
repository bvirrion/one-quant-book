"""Chart data for Book 12, chapter 14: accuracy of the clean and contaminated models by period; retrieval by method."""
import pathlib

import ml_llm as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "14-large-language-models-in-finance"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = m.contamination()
    with open(OUT / "contamination.csv", "w") as f:
        f.write("i,period,clean,cleananon,contam,contamanon\n")
        for i, p in enumerate(m.PERIODS):
            f.write(f"{i},{p.replace(' ', '')},{100 * c['clean'][p][0]:.1f},{100 * c['clean'][p][1]:.1f},"
                    f"{100 * c['contaminated'][p][0]:.1f},{100 * c['contaminated'][p][1]:.1f}\n")
    ceiling = 100 * m.planted_accuracy()[2]
    with open(OUT / "ceiling.csv", "w") as f:
        f.write(f"x,y\n-0.5,{ceiling:.1f}\n2.5,{ceiling:.1f}\n")
    r = m.retrieval()
    with open(OUT / "retrieval.csv", "w") as f:
        f.write("i,method,same,other\n")
        for i, k in enumerate(r):
            f.write(f"{i},{k},{100 * r[k]['same word']:.1f},{100 * r[k]['other word']:.1f}\n")


if __name__ == "__main__":
    main()
