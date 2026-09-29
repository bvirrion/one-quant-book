"""Numbers gate: every number printed in Book 14, chapter 14 (text and solutions)."""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_wireless as w  # noqa: E402

rl, gm = w.rl, w.gm


def r(x, k=1):
    return round(x, k)


def test_tables():
    g = [(x["d_km"], x["f_ghz"], r(x["bulge_m"]), r(x["fresnel_m"]), r(x["tower_m"])) for x in w.geometry_rows()]
    assert g == [(30, 6, 13.2, 19.4, 42.6), (30, 11, 13.2, 14.3, 37.5), (50, 6, 36.8, 25.0, 71.8),
                 (50, 11, 36.8, 18.5, 65.3), (70, 6, 72.1, 29.6, 111.7), (70, 11, 72.1, 21.8, 104.0)]
    b = [(x["f_ghz"], r(x["gain_dbi"]), r(x["fspl_db"]), r(x["rx_dbm"]), r(x["margin_db"]), r(x["rain_full"]), r(x["rain_cell"]))
         for x in w.budget_rows()]
    assert b == [(6, 38.9, 143.6, -38.9, 31.1, 63.5, 196.0), (11, 44.1, 148.8, -33.6, 36.4, 18.4, 80.4),
                 (18, 48.4, 153.1, -29.3, 40.7, 8.1, 42.3), (80, 61.4, 166.1, -16.4, 53.6, 0.7, 8.5)]
    assert round(b[0][5]) == 64


def test_text_numbers():
    assert round(rl.gamma_db_km(2.5, 80) / rl.gamma_db_km(2.5, 6), -1) == 740            # figure 14.2's spread
    assert r(rl.gamma_db_km(50, 11), 2) == 2.05 and r(2 * 6371.0 / 1000, 2) == 12.74 and r(math.sqrt(299.8), 2) == 17.31
    assert r(rl.bulge_m(15, 15, 1.0) * 1, 1) == r(30 * 30 / 50.96, 1)
    assert r(w.D_KM, 1) == 1180.9 and r(w.FIBRE_US / 1e3, 3) == 6.911 and r((w.FIBRE_US - w.RADIO_US) / 1e3, 2) == 2.93
    L = w.route()
    assert len(L) == 20 and round(L[0]) == 59
    s = {x.id: x for x in gm.load_sites(w.ROOT / "data" / "networks" / "sites.csv")}
    d = gm.geodesic_m(s["ny4"].lat, s["ny4"].lon, s["ld4"].lat, s["ld4"].lon)
    assert (round(d / 1e3), r(gm.floor_us(d) / 1e3, 2), r(gm.floor_us(d, "fibre") / 1e3, 2)) == (5551, 18.52, 27.07)
    p = 2 * math.hypot(d / 2e3, 300)
    assert r(100 * (p / (d / 1e3) - 1), 1) == 0.6 and round(29.475 - gm.floor_us(p * 1e3) / 1e3) == 11


def test_storm_and_year():
    m = {(f, p): w.minutes_on_fibre(f, p) for f in (6, 11, 18) for p in (50, 100, 150)}
    assert [m[(11, p)] for p in (50, 100, 150)] == [5, 21, 26]
    assert [m[(6, p)] for p in (50, 100, 150)] == [0, 0, 7] and [m[(18, p)] for p in (50, 100, 150)] == [22, 29, 31]
    assert len(w.storm()) == 38 and 30 / 0.8 == 37.5
    h = rl.Hop(w.route()[0], 11)
    down = 1 - rl.availability(h, w.exceed)
    assert r(100 * down, 3) == 0.047 and r(down * 8766, 1) == 4.1
    route_down = 1 - (1 - down) ** 20
    assert r(100 * route_down, 2) == 0.94 and round(route_down * 8766) == 82 and r(100 * route_down, 1) == 0.9
    assert (r(rl.bulge_m(L2 := h.d_km / 2, L2), 1), r(rl.fresnel_m(L2, L2, 11), 1), r(rl.tower_m(h.d_km, 11), 1)) == (51.3, 20.1, 81.4)
    assert (r(rl.fspl_db(h.d_km, 11), 1), r(rl.rx_dbm(h), 1), r(rl.fade_margin_db(h), 1)) == (148.7, -33.5, 36.5)
    assert (r(rl.critical_rain(h), 1), r(rl.critical_rain(h, 10), 1)) == (18.7, 80.6)


def test_exercises():
    assert (r(rl.bulge_m(20, 20), 1), r(rl.fresnel_m(20, 20, 11), 1)) == (23.5, 16.5)
    assert (r(rl.gamma_db_km(25, 6), 3), r(rl.gamma_db_km(25, 18), 2)) == (0.118, 2.30)
    assert round(rl.gamma_db_km(25, 18) / rl.gamma_db_km(25, 6)) == 20
    h2 = rl.Hop(2 * w.route()[0], 11)
    assert (r(20 * math.log10(2), 2), r(rl.critical_rain(h2), 1)) == (6.02, 9.1)
    first = next(p for p in range(20, 80) if w.minutes_on_fibre(11, p) > 0)
    assert first == 48
    assert r(0.9995 ** 20, 3) == 0.990 and round((1 - 0.9995 ** 20) * 8766) == 87


def test_small_runs():
    assert len(w.critical_curve(range(10, 31, 10))) == 3 and w.exceed(0) == 0.05
