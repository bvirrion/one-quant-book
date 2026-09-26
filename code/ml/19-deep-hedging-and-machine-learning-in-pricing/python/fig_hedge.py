"""Chart data for Book 12, chapter 19: indifference price against the cost level; hedging bands across moneyness."""
import pathlib

import ml_hedge as m
import numpy as np

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "19-deep-hedging-and-machine-learning-in-pricing"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    h = m.hedging()
    with open(OUT / "indifference.csv", "w") as f:
        f.write("cost,deep,bs,ww\n")
        for c in m.COSTS:
            r = h[c]
            f.write(f"{1e4 * c:.0f},{r['deep hedge']['entropic']:.4f},{r['Black-Scholes delta']['entropic']:.4f},"
                    f"{r['Whalley-Wilmott']['entropic']:.4f}\n")
    c = m.COSTS[-1]
    net, ww = m.hedger(c), m.ww_policy(m.atm_vol(), m.K, m.T, c, 1.0)
    bs = m.bs_policy(m.atm_vol(), m.K, m.T)
    with open(OUT / "bands.csv", "w") as f:
        f.write("spot,deeplo,deephi,wwlo,wwhi,delta\n")
        for s in np.linspace(92.0, 108.0, 33):
            dl, dh = m.band(net, 0.5, s, m.K)
            wl, wh = m.band(ww, 0.5, s, m.K)
            d, _ = m.band(bs, 0.5, s, m.K)
            f.write(f"{s:.2f},{dl:.4f},{dh:.4f},{wl:.4f},{wh:.4f},{d:.4f}\n")


if __name__ == "__main__":
    main()
