import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_overfit import cpcv, cpcv_paths, cscv, min_backtest_length, purged_kfold, walk_forward


def test_cscv_noise_and_skill():
    rng = np.random.default_rng(0)
    noise = rng.standard_normal((1600, 50))
    r = cscv(noise, 16, max_splits=2000)
    assert 0.35 < r["pbo"] < 0.65 and r["slope"] < 0.3                  # selection on noise: a coin toss
    skill = noise.copy()
    skill[:, 7] += 0.3                                                   # one strategy with a real edge
    s = cscv(skill, 16, max_splits=2000)
    assert s["pbo"] < 0.01 and np.all(s["oos_of_best"] > 0)


def test_purged_kfold_and_embargo():
    start = np.arange(20)
    end = start + 2                                                      # each label uses three periods
    folds = purged_kfold(start, end, k=4, embargo=0)
    train, test = folds[1]
    assert list(test) == [5, 6, 7, 8, 9]
    assert list(train) == [0, 1, 2, 12, 13, 14, 15, 16, 17, 18, 19]     # 3, 4 overlap 5; 10, 11 start inside
    tr_e, _ = purged_kfold(start, end, k=4, embargo=2)[1]
    assert 12 not in tr_e and 13 not in tr_e and 14 in tr_e             # the embargo drops the two after the fold


def test_cpcv_and_walk_forward():
    start = np.arange(60)
    splits = cpcv(start, start, n_folds=6, n_test=2)
    assert len(splits) == 15 and cpcv_paths(6, 2) == 5 and cpcv_paths(10, 2) == 9
    assert all(len(np.intersect1d(tr, te)) == 0 for tr, te in splits)
    wf = walk_forward(100, 40, 20)
    assert [(tr[0], tr[-1], te[0], te[-1]) for tr, te in wf] == [(0, 39, 40, 59), (20, 59, 60, 79), (40, 79, 80, 99)]
    assert walk_forward(100, 40, 20, anchored=True)[2][0][0] == 0


def test_min_backtest_length():
    y = min_backtest_length(1000, 1.0)
    assert 5 < y < 12 and min_backtest_length(10, 1.0) < y < min_backtest_length(1000, 0.5)
    assert math.isclose(min_backtest_length(1000, 1.0) * 4, min_backtest_length(1000, 0.5), rel_tol=1e-6)
