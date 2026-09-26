"""Chart data for Book 12, chapter 17: learning curves against the optimum; bandit regret."""
import pathlib

import ml_rl as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "17-reinforcement-learning-foundations"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lc = m.learning_curves()
    cols = {"Q-learning": "q", "SARSA": "sarsa", "REINFORCE": "reinforce", "actor-critic": "ac"}
    with open(OUT / "curves.csv", "w") as f:
        f.write("episodes," + ",".join(cols.values()) + "\n")
        for i, n in enumerate(m.CHECKS):
            f.write(f"{n}," + ",".join(f"{lc[k][i]:.4f}" for k in cols) + "\n")
    b = m.bandits()
    bc = {"epsilon 0.1": "eps1", "epsilon 0.01": "eps01", "UCB, c = 1.41": "ucb141", "UCB, c = 1": "ucb1"}
    with open(OUT / "regret.csv", "w") as f:
        f.write("t," + ",".join(bc.values()) + "\n")
        for t in range(99, 10000, 100):
            f.write(f"{t + 1}," + ",".join(f"{b[k][0][t]:.1f}" for k in bc) + "\n")


if __name__ == "__main__":
    main()
