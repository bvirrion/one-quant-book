import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_earnstrat import announcement_move, calendar, event_book, event_car  # noqa: E402


def test_calendar_and_book_by_hand():
    flag, s = calendar([(1, 0, 2.0), (2, 1, -1.5), (2, 2, 0.5)], 6, 3)
    assert flag.sum() == 3 and np.isnan(s[0, 0]) and s[2, 1] == -1.5
    W = event_book(flag, s, np.ones((6, 3), bool), hold=3, threshold=1.0)
    assert W[0].tolist() == [0, 0, 0]
    assert W[1].tolist() == [0.5, 0, 0] and W[2].tolist() == [0.5, -0.5, 0] and W[3].tolist() == [0.5, -0.5, 0]
    assert W[4].tolist() == [0, -0.5, 0] and W[5].tolist() == [0, 0, 0]
    D = event_book(flag, s, np.ones((6, 3), bool), hold=3, threshold=1.0, delay=1)
    assert D[1].tolist() == [0, 0, 0] and D[2].tolist() == [0.5, 0, 0] and D[5].tolist() == [0, -0.5, 0]


def test_moves_and_car():
    ret = np.full((10, 2), 0.01)
    flag = np.zeros((10, 2), bool)
    flag[5, 0] = True
    ret[5, 0] = 0.05
    assert abs(announcement_move(ret, flag) - 5.0) < 1e-12
    s = np.where(flag, 1.0, np.nan)
    car = event_car(ret, flag, s, 2, 2)
    assert np.allclose(car["positive"], [0.01, 0.02, 0.07, 0.08, 0.09]) and np.allclose(car["negative"], 0)
