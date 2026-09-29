import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_fxlinks as fx  # noqa: E402

T = fx.sites()


def test_venues_and_sites():
    v = fx.load_venues()
    assert {x.site for x in v} <= set(T) and sum(x.role == "matching" for x in v) == 4
    assert fx.one_way_ms("ld4", "ld4", 1.5, T) == 0.0
    assert 40 < fx.one_way_ms("ld4", "ty3", 1.0, T) < 50


def test_equal_paths_need_no_hold():
    p = fx.Paths(proc_ms=0.0)
    for o in ("ld4", "ny5", "ty3"):
        for v in ("ld4", "ny5", "ty3"):
            assert fx.hold_ms(o, "ld4", v, p, T) == 0.0
    assert fx.staleness_ms("ty3", "ld4", "ty3", p, T) == 2 * fx.one_way_ms("ty3", "ld4", 1.5, T)


def test_slow_information_path():
    p = fx.Paths(info=2.5, proc_ms=0.0)
    h = fx.hold_ms("ty3", "ld4", "ty3", p, T)
    assert abs(h - fx.one_way_ms("ty3", "ld4", 1.0, T)) < 1e-9
    c = fx.caught("ty3", "ld4", "ty3", p, [0.0, h + 5], n=2000, table=T)
    assert c[0] < 0.01 and c[1] > 0.99


def test_windows_and_path():
    assert fx.stale_window_ms({"a": 3.0, "b": 1.0}) == {"a": 2.0, "b": 0.0}
    assert fx.order_path_ms("ld4", "ld4", {"gateway": 0.02, "credit": 0.01}, 1.5, T) == 0.03
