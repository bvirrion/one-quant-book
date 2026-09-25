import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_macrobook import ViewConfig, bachelier_receiver, expressions, stopped_correct  # noqa: E402


def test_bachelier_at_the_money_and_parity():
    assert abs(bachelier_receiver(0.0, 100.0, 1.0) - 100 / math.sqrt(2 * math.pi)) < 1e-9
    k, sd = -25.0, 60.0
    assert abs(bachelier_receiver(k, sd, 1.0) - bachelier_receiver(-k, sd, 1.0) - k) < 1e-9   # receiver minus payer at -k


def test_expressions_on_hand_made_paths():
    cfg = ViewConfig()
    paths = np.array([np.linspace(0, -100, 127), np.concatenate([np.linspace(0, 30, 64), np.linspace(30, -80, 63)])])
    e = expressions(paths, cfg)
    assert e["futures, stop 25"][1] == -1.0 and e["futures, stop 25"][0] == 100 / 25
    assert e["futures, stop 50"][1] == 80 / 50
    assert stopped_correct(paths, cfg, 25.0) == 0.5 and stopped_correct(paths, cfg, 50.0) == 0.0
