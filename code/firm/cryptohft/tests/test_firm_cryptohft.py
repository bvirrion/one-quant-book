import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_cryptohft as ch  # noqa: E402


def _week(**kw):
    return ch.Week(seed=4, days=1, cascade_day=None, **kw)


def test_parts_add_up_and_fresh_quotes_are_not_picked_off():
    w = _week()
    r = ch.run(w, requote_per_s=1.0)
    parts = sum(r[k] for k in ("spread", "adverse", "hedge", "fees", "funding", "cascade"))
    assert math.isclose(parts, r["total"])
    assert abs(r["adverse"]) < 1e-6 and r["spread"] > 0 and r["hedge"] < 0 and r["fees"] > 0


def test_stale_quotes_cost_and_budget():
    w = _week()
    fast, slow = ch.run(w, requote_per_s=1.0), ch.run(w, requote_per_s=0.1)
    assert slow["adverse"] < fast["adverse"] and slow["requests"] < fast["requests"]
    assert math.isclose(ch.budget_from(ch.rl.binance_like(), 1), 200000 / 86400 / 2)


def test_cascade_absorption():
    w = ch.Week(seed=4, days=1, cascade_day=0)
    pull = ch.run(w, absorb=False)
    absorb = ch.run(w, absorb=True, absorb_limit=5e6, absorb_from_bp=40.0)
    assert absorb["cascade"] > pull["cascade"]
    rec = ch.run(w, absorb=True, absorb_limit=5e6, absorb_from_bp=40.0, record=(w.t0, w.t0 + 600))
    assert max(p[2] for p in rec["path"]) > 1e6
