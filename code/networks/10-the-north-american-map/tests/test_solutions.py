"""Numbers gate: every number printed in Book 14, chapter 10 (text and solutions)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_map as m  # noqa: E402

g = m.gm


def r(x, n=1):
    return round(x, n)


def test_pairs_table():
    rows = {(p["a"], p["b"]): p for p in m.pair_rows()}
    expect = {("mahwah", "carteret"): (55.6, 185.4, 185.4, 271.0), ("mahwah", "ny4"): (34.5, 114.9, 115.0, 168.0),
              ("ny4", "carteret"): (25.9, 86.3, 86.3, 126.2), ("aurora", "carteret"): (1180.9, 3939.0, 3940.1, 5758.8),
              ("aurora", "mahwah"): (1179.0, 3932.6, 3933.8, 5749.4), ("aurora", "ny5"): (1191.1, 3973.1, 3974.3, 5808.7),
              ("aurora", "cermak"): (52.3, 174.5, 174.5, 255.1), ("cermak", "carteret"): (1129.2, 3766.7, 3767.8, 5506.9),
              ("markham", "mahwah"): (523.7, 1747.0, 1747.6, 2554.2), ("markham", "ny4"): (550.2, 1835.3, 1835.9, 2683.3),
              ("markham", "carteret"): (553.1, 1844.9, 1845.4, 2697.2)}
    for k, v in expect.items():
        p = rows[k]
        assert (r(p["km"]), r(p["vacuum_us"]), r(p["air_us"]), r(p["fibre_us"])) == v, k
    assert r(m.distance("ny4", "ny5") * 1e-3, 2) == 0.32
    assert round(2 * rows[("mahwah", "carteret")]["vacuum_us"]) == 371


def test_routes_table():
    rows = {x["label"]: x for x in m.route_rows()}
    expect = {"Quincy 2016 to Carteret": (3.940, 1.011, 42), "Quincy 2016 to Mahwah": (3.934, 1.013, 52),
              "ICE Toronto to Mahwah": (1.748, 1.082, 142), "ICE Toronto to NY4": (1.836, 1.084, 154),
              "ICE Toronto to Carteret": (1.845, 1.111, 205), "Spread 2010 (6.65 ms)": (5.507, 1.208, 1143),
              "Spread later (6.55 ms)": (5.507, 1.189, 1043)}
    for k, (floor, rho, ex) in expect.items():
        x = rows[k]
        assert (round(x["floor_us"] / 1000, 3), round(x["factor"], 3), round(x["excess_us"])) == (floor, rho, ex), k
    assert r(rows["Quincy 2016 to Carteret"]["excess_km"]) == 12.5 and r(rows["Quincy 2016 to Mahwah"]["excess_km"]) == 15.7
    assert round(rows["Spread 2010 (6.65 ms)"]["excess_km"]) == 234
    assert round(rows["Quincy 2016 to Carteret"]["factor"] - 1, 3) == 0.011  # "1.1% above"


def test_text_numbers():
    t = m.sites()
    d = m.distance("aurora", "carteret", t)
    assert r(d / 1e3, 2) == 1180.87 and r(g.floor_us(d) / 1e3, 2) == 3.94 and r(g.floor_us(d, "fibre") / 1e3, 2) == 5.76
    assert r(m.chord_saving_m("aurora", "carteret") / 1e3, 2) == 1.68 and r(m.chord_saving_m("aurora", "carteret") / g.C0 * 1e6) == 5.6
    assert r(1e9 / g.C0, 3) == 3.336 and r(1e9 / g.C0 * g.N_FIBRE, 3) == 4.877 and r(1e9 / g.C0, 4) == 3.3356 and r(100 * (g.N_FIBRE - 1)) == 46.2
    assert r(1e6 / g.C0 * (g.N_AIR - 1) * 1e6, 1) == 1.0
    assert r(d * (1.0003 - 1.00027) / g.C0 * 1e6, 2) == 0.12
    assert r((g.floor_us(d, "fibre") - g.floor_us(d, "air")) / 1e3, 2) == 1.82
    hav = g.haversine_m(t["aurora"].lat, t["aurora"].lon, t["carteret"].lat, t["carteret"].lon)
    assert r((hav - d) / 1e3, 2) == -2.97 and r(hav / 1e3, 2) == 1177.90 and r(100 * m.spherical_error("aurora", "carteret"), 2) == -0.25
    assert r((d - hav) * g.N_AIR / g.C0 * 1e6, 1) == 9.9 and r(100 * m.spherical_error("mahwah", "carteret"), 2) == 0.12
    # Markham: 1.747 ms one way, round trip at least 3.49 ms; rack-to-rack minus radio-to-radio
    mm = m.distance("markham", "mahwah", t)
    assert r(g.floor_us(mm) / 1e3, 3) == 1.747 and int(2 * g.floor_us(mm) / 10) / 100 == 3.49
    assert (round(1.89 - 1.88, 2), round(2.05 - 2.03, 2)) == (0.01, 0.02)
    assert r(2 * g.floor_us(m.distance("markham", "carteret", t)) / 1e3, 2) == 3.69
    # synchronised routing from Carteret
    ny5 = g.floor_us(m.distance("carteret", "ny5", t), "fibre")
    mah = g.floor_us(m.distance("carteret", "mahwah", t), "fibre")
    assert (r(ny5), r(mah), round(mah - ny5)) == (126.6, 271.0, 144) and r(m.distance("carteret", "ny5", t) / 1e3, 2) == 25.96
    # site error
    assert r(1e3 / g.C0 * 1e6, 1) == 3.3 and r(g.floor_us(3e3), 1) == 10.0 and r(g.floor_us(3e3, "fibre"), 1) == 14.6
    assert round(0.3e3 / g.C0 * 1e6) == 1


def test_laughlin_cross_check():
    t = m.sites()
    assert (round(t["aurora"].lat, 2), round(t["aurora"].lon, 2)) == (41.80, -88.24)
    assert abs(t["carteret"].lat - 40.58) < 0.01 and abs(t["carteret"].lon + 74.25) < 0.01
    rounded = g.geodesic_m(41.80, -88.24, 40.58, -74.25)
    sph = g.haversine_m(41.80, -88.24, 40.58, -74.25)
    d = m.distance("aurora", "carteret", t)
    assert (r(sph / 1e3), r(rounded / 1e3)) == (1177.2, 1180.1) and abs(d / 1e3 - 1179) < 2
    assert (r(rounded / 1e3 - 1179, 2), r((d - rounded) / 1e3, 2)) == (1.13, 0.74)
    assert round(g.floor_us(d) - 3930) == 9 and abs(g.floor_us(d) - 3935) < 6  # "3.93 ms agrees to 6 us" (3.93 rounds 3.925-3.935)


def test_problem():
    t = m.sites()
    d = m.distance("aurora", "carteret", t)
    assert (r(2 * g.floor_us(d, "fibre") / 1e3, 2), r(2 * g.floor_us(d) / 1e3, 2)) == (11.52, 7.88)
    met, cc = m.distance("aurora", "cermak", t), m.distance("cermak", "carteret", t)
    rho = 6650 / g.floor_us(cc, "fibre")
    leg = g.floor_us(met, "fibre") * rho
    assert (r(leg), round((6650 + leg) / 1e3, 3), round((6650 + leg) / g.floor_us(d, "fibre"), 3)) == (308.0, 6.958, 1.208)
    assert r((6650 - 6550) * 1e-6 * g.C0 / g.N_FIBRE / 1e3) == 20.5
    assert round(g.floor_us(d, "fibre") - 3982) == 1777 and r(3982 - g.floor_us(d, "air")) == 41.9
    assert round(3982 / g.floor_us(d), 3) == 1.011
    assert r(100 * (1 - g.N_AIR / g.N_FIBRE)) == 31.6
    assert r(m.distance("ny4", "carteret", t) / 1e3) == 25.9 and r(m.distance("mahwah", "ny4", t) / 1e3) == 34.5


def test_small_runs():
    pts = dict((i, (x, y)) for i, x, y in m.map_points("nj"))
    assert set(pts) == {"mahwah", "ny4", "carteret"} and pts["mahwah"][1] > pts["carteret"][1]
    assert all(s.source.startswith("networks/") for s in m.sites().values())
