import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_exposure as f


class Flat:
    def __init__(self, r):
        self.r = r

    def df_t(self, t):
        return math.exp(-self.r * t)


MKT = f.Market(Flat(0.04), Flat(0.02), kappa=0.05, sigma=0.01, fx0=1.1, fx_vol=0.1)


def test_fixture_matches_the_cpp_and_rust_twins():
    r = f.aggregate(list(f.fixture()), threshold=2.0, mta=1.0, lag=1, q=0.75)
    assert abs(r["ee"][2] - 1.0751127413) < 1e-9 and abs(r["ene"][12] + 1.7316228823) < 1e-9
    r = f.aggregate(list(f.fixture()), threshold=0.0, mta=0.0, lag=2, ia=1.5, q=0.75)
    assert abs(r["pfe"][6] - 4.2045873756) < 1e-9


def test_par_trades_are_worth_zero_and_bonds_and_fx_are_martingales():
    sc = f.simulate(MKT, 5.0, 12, 20_000, seed=3)
    k = f.usd_par_rate(MKT.usd, 5)
    assert abs(f.Swap(1.0, k, 5).values(sc)[:, 0].mean()) < 1e-12
    t = sc.times[24]
    assert abs(sc.fx[:, 24].mean() / (1.1 * math.exp(-0.02 * t) / math.exp(-0.04 * t)) - 1) < 2e-3
    # deflated bond: E[exp(-int r) P(t, T)] = P(0, T), with the bank account along the grid
    r = np.array([-math.log(MKT.usd.df_t(sc.times[j + 1]) / MKT.usd.df_t(sc.times[j])) * 12
                  for j in range(24)])[None, :] + sc.x[:, :24]
    defl = np.exp(-(r / 12).sum(axis=1))
    assert abs((defl * sc.usd_bond(24, 5.0)).mean() - MKT.usd.df_t(5.0)) < 2e-3


def test_collateral_and_netting_reduce_exposure():
    sc = f.simulate(MKT, 5.0, 26, 4000)
    a = f.Swap(1e6, f.usd_par_rate(MKT.usd, 5), 5).values(sc)
    b = f.Swap(1e6, f.usd_par_rate(MKT.usd, 5), 5, receive_fixed=False).values(sc) * 0.5
    net = f.aggregate([a, b])["ee"].max()
    assert net < f.aggregate([a])["ee"].max() + f.aggregate([b])["ee"].max()
    c10 = f.aggregate([a], threshold=0.0, mta=0.0, lag=1)["ee"][:-1].max()
    c20 = f.aggregate([a], threshold=0.0, mta=0.0, lag=2)["ee"][:-1].max()
    assert c10 < c20 < f.aggregate([a])["ee"].max()
