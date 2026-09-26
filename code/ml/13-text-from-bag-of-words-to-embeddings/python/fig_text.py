"""Chart data for Book 12, chapter 13: information coefficient against training size; cosines of word embeddings."""
import pathlib

import ml_text as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "13-text-from-bag-of-words-to-embeddings"
KEYS = ("dictionary", "tf-idf unigrams", "tf-idf n-grams", "supervised words", "embeddings", "event rules", "truth")
COLS = ("dictionary", "tfidf1", "tfidf2", "supervised", "embeddings", "events", "truth")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lc = m.learning_curve()
    with open(OUT / "learning.csv", "w") as f:
        f.write("docs," + ",".join(COLS) + "\n")
        for n, r in lc.items():
            f.write(f"{n}," + ",".join(f"{r[k]:.4f}" for k in KEYS) + "\n")
    with open(OUT / "pairs.csv", "w") as f:
        f.write("i,pair,kind,cosine\n")
        for i, (a, b, kind, c) in enumerate(m.pairs()):
            f.write(f"{i},{a}--{b},{kind.replace(' ', '')},{c:.4f}\n")


if __name__ == "__main__":
    main()
