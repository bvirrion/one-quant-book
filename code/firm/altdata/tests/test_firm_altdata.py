import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_altdata import card_panel, delivery_check, first_seen, normalise, rake, resolve, validate  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "pit"))
from firm_pit import Store  # noqa: E402

GOOD = {"quarter": 3, "merchant": "SQ *X", "age": 1, "region": 0, "spend": 10.0, "panelists": 5}


def test_validation_reasons():
    rows = [dict(GOOD), dict(GOOD), {k: v for k, v in GOOD.items() if k != "spend"}, GOOD | {"spend": -1.0},
            GOOD | {"panelists": "5"}, GOOD | {"age": 7}, GOOD | {"quarter": True}]
    clean, rej = validate(rows)
    assert clean == [GOOD]
    assert [why for _, why in rej] == ["duplicate", "missing spend", "range spend", "type panelists", "range age",
                                       "type quarter"]


def test_delivery_check():
    assert delivery_check(None, 5.0) and delivery_check(100.0, 150.0)
    assert not delivery_check(100.0, 210.0) and not delivery_check(100.0, 40.0)


def test_resolution():
    aliases = {"Borealis Retail": 1, "Borealis Stores": 2, "Cobalt Foods": 3}
    out = resolve(["SQ *BOREALIS RET", "BOREALI RETA STR 12", "BOREALIS 5120", "COBALT FOODS #99", "DELTA AIR LINES"],
                  aliases)
    assert out["SQ *BOREALIS RET"][:3:2] == (1, "matched") and out["BOREALI RETA STR 12"][0] == 1
    assert out["BOREALIS 5120"][2] == "review" and out["COBALT FOODS #99"][:3:2] == (3, "matched")
    assert out["DELTA AIR LINES"][2] == "none"
    assert normalise("TST* Cobalt Foods Inc #12") == "cobalt foods"


def test_rake_matches_margins():
    rng = np.random.default_rng(0)
    n = rng.integers(10, 200, (3, 2)).astype(float)
    w = rake(n, [0.3, 0.35, 0.35], [0.49, 0.51])
    wc = w * n
    assert np.allclose(wc.sum(1) / wc.sum(), [0.3, 0.35, 0.35]) and np.allclose(wc.sum(0) / wc.sum(), [0.49, 0.51])
    even = np.outer([30.0, 35.0, 35.0], [49.0, 51.0])
    assert np.allclose(rake(even, [0.3, 0.35, 0.35], [0.49, 0.51]), 1.0)


def test_first_seen_separates_backfill():
    s = Store()
    for q in range(4):
        s.put("A", "spend", q, 4, 1.0)
    for q in range(4, 8):
        s.put("A", "spend", q, q + 1, 1.0)
    assert [q for q in range(8) if first_seen(s, "A", "spend", q) - q > 1] == [0, 1, 2]
    assert first_seen(s, "A", "spend", 99) is None


def test_card_panel_truth():
    w = card_panel(n_firms=10, quarters=8, launch=4, partner_change=6, seed=1)
    est = np.einsum("iqar,ar->iq", w["panel"] / w["panelists"][None], w["pop"])
    assert np.median(np.abs(est / w["sales"] - 1)) < 0.05
    assert w["panelists"][5].sum() == 50000 and w["panelists"][6].sum() == 30000
    assert len(set(w["names"])) == 10
