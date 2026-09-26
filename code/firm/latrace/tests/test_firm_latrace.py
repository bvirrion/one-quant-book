import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_latrace as lr  # noqa: E402


def test_symmetric_bump_changes_nothing_and_asymmetric_protects():
    c = lr.race("continuous", seed=3)
    s = lr.race("symmetric", d=350.0, seed=3)
    a = lr.race("asymmetric", d=350.0, seed=3)
    assert c["p_sniped"] == s["p_sniped"] and 0.5 < c["p_sniped"] < 0.95
    assert a["p_sniped"] < 1e-3


def test_faster_provider_is_sniped_less_and_batches_help():
    slow = lr.race("continuous", lp_median=80.0, seed=4)["p_sniped"]
    fast = lr.race("continuous", lp_median=20.0, seed=4)["p_sniped"]
    assert fast < slow
    b = lr.race("batch", tau=1000.0, seed=4)
    assert b["p_sniped"] < 0.1 * lr.race("continuous", seed=4)["p_sniped"]


def test_tax_is_probability_times_the_stale_edge():
    r = lr.race("continuous", jump=2.0, half=0.5, seed=5)
    assert abs(r["tax"] - 1.5 * r["p_sniped"]) < 1e-12
