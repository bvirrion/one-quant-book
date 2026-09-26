"""Chart data for Book 12, chapter 18: schedules in the thin-liquidity world; gaps to the optimum in three worlds."""
import pathlib

import ml_rltrade as m

OUT = (pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml"
       / "18-reinforcement-learning-for-execution-and-market-making")
COLS = {"Almgren-Chriss (model)": "acmodel", "TWAP": "twap", "DQN": "dqn", "DQN, noisy reward": "noisy",
        "DQN, randomised": "dr"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    eta = m.WORLDS["impact x3"]
    sched = {k: f(eta) for k, f in m.agents().items()} | {"optimum": m.optimum(eta)}
    with open(OUT / "schedules.csv", "w") as f:
        f.write("step,optimum," + ",".join(COLS.values()) + "\n")
        for i in range(m.ENV.n + 1):
            f.write(f"{i},{sched['optimum'][i]:.4f}," + ",".join(f"{sched[k][i]:.4f}" for k in COLS) + "\n")
    ex = m.execution()
    with open(OUT / "gaps.csv", "w") as f:
        f.write("i,world," + ",".join(COLS.values()) + "\n")
        for i, w in enumerate(m.WORLDS):
            f.write(f"{i},{w.replace(' ', '')}," + ",".join(f"{ex[w][k]:.3f}" for k in COLS) + "\n")


if __name__ == "__main__":
    main()
