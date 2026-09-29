"""Numbers gate: every number printed in Book 14, chapter 29 (text and solutions)."""
import csv
import dataclasses
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_plan as n  # noqa: E402

cp = n.cp


def test_latency_table_and_fix():
    r = n.report()
    t = {x["venue"]: x for x in r["latency"]}
    assert round(t["NYSE equities (Mahwah)"]["achieved_us"], 1) == 35.6
    assert t["CME data (Aurora to Mahwah)"]["achieved_us"] == 3986.0
    assert round(t["CME orders (Mahwah to Aurora)"]["achieved_us"] / 1000, 2) == 7.48
    assert round(t["Binance (AWS Tokyo)"]["achieved_us"] / 1000, 2) == 2.40
    assert [x["met"] for x in r["latency"]] == [True, True, True, False]
    assert [round(100 * x["achieved_us"] / x["target_us"]) for x in r["latency"]] == [89, 95, 93, 240]
    f = r["fixes"]
    assert [x["option"] for x in f] == ["endpoint_same", "endpoint_other"]
    assert (round(f[0]["achieved_us"] / 1000, 2), round(f[1]["achieved_us"] / 1000, 2)) == (0.44, 0.80)
    assert round(f[0]["extra_annual"], 2) == 122.64
    v = dataclasses.replace(n.VENUES[2], factor=1.2)
    assert round(cp.latency_us(v, n.PLAN) / 1000, 2) == 6.90


def test_budget_and_checks():
    b = n.report()["budget"]
    assert (round(b["monthly"]), round(b["one_time"]), round(b["annual"])) == (68812, 39500, 1017289)
    by = {k: round(v) for k, v in b["by_category"].items()}
    assert by == {"colocation": 146333, "connectivity": 567167, "market data": 109667, "cloud": 15747,
                  "disaster recovery": 178375}
    assert round(100 * by["connectivity"] / b["annual"]) == 56 and round(100 * 293000 / b["annual"], 1) == 28.8
    assert n.report()["checks"] == {"unsourced": ["wave_mah_aur"], "stale": []}
    s = {k: round(v) for k, v in n.sensitivities().items()}
    assert s == {"second 10 Gb LCN connection": 366250, "12 kW instead of 8": 72000, "no backup IP circuit": -38542,
                 "wavelength price 50% higher": 152083, "four Tokyo instances": 15747}
    assert 8 * 1200 == 9600 and round(100 * 2000 / 22000, 1) == 9.1


def test_availability_and_export():
    a = n.access_availability()
    assert (round(100 * a["lcn only"], 3), round(100 * a["lcn and ip"], 3)) == (99.9, 99.982)
    rows = list(csv.DictReader(open(n.ROOT / "code" / "firm" / "connplan" / "data" / "cost_table.csv")))
    assert len(rows) == 9 and sum(r["source"] == "" for r in rows) == 1
    assert [round(float(r["annual_usd"])) for r in rows] == [1667, 115200, 29467, 293000, 30833, 243333, 73667, 36000, 15747]


def test_small_runs():
    assert len(n.PRICES) == 10 and n.PLAN.term_months == 36
