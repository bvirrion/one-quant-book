"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 2 (text and solutions)."""
import csv
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "tickcap"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "feedhandler"))
from firm_tickcap import RECORD, StorageModel, compressed_size
from pl_tickcap import OPRA_MSGS_PER_DAY, PRICES, economics, study

MEASURED = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/02-capturing-and-storing-tick-data/measured_compress.csv"


def r(x, d=2):
    return round(float(x), d)


def test_small_runs(tmp_path):
    s = study(0.02, str(tmp_path / "d"))
    assert s["messages"] > 1000 and s["counters"]["duplicates"] > 0.4 * s["counters"]["packets"]
    pm = s["per_msg"]
    assert pm["normalised"] == 56.0
    assert pm["delta columns, zlib 6"] < pm["normalised, zlib 6"] < pm["normalised"] < pm["raw capture"]
    assert pm["raw, zlib 6"] < pm["raw capture"]
    e = economics(pm)
    assert e["raw capture, both lines"]["PB_year"] == pytest.approx(2 * e["raw capture, one line"]["PB_year"])


@pytest.mark.reference
def test_session_numbers():
    s = study()
    assert s["messages"] == 258535 and s["bytes_A"] == 15773858 and s["bytes_B"] == 15642035
    c = s["counters"]
    assert (c["packets"], c["duplicates"], c["gap_messages"], len(s["gaps"])) == (503024, 255899, 8, 4)
    assert r(100 * s["kinds"]["A"] / s["messages"], 1) == 49.3 and r(100 * s["kinds"]["D"] / s["messages"], 1) == 47.3
    assert r(100 * s["kinds"]["E"] / s["messages"], 1) == 3.4
    pm, cr = s["per_msg"], s["ratio"]
    assert [r(pm[k], 1) for k in pm] == [61.0, 18.4, 56.0, 15.2, 15.0, 11.9]
    assert (r(cr["raw, zlib 6"]), r(cr["normalised, zlib 6"]), r(cr["delta columns, zlib 6"])) == (3.32, 3.67, 4.70)
    assert s["partitions"][1] == 811160 and sum(s["partitions"].values()) == 14477960
    assert r(100 * 811160 / 14477960, 1) == 5.6 and 811160 // RECORD.itemsize == 14485
    # exercise 1: framing share
    assert r(15773858 / 258535, 1) == 61.0 and r(100 * 34 / (15773858 / 258535), 1) == 55.7
    # exercise 2
    assert r(56 / 15.24) == 3.67
    # exercise 7: sorted by instrument
    rec = s["rec"]
    srt = rec[np.lexsort((rec["seq"], rec["locate"]))]
    assert r(rec.nbytes / compressed_size(srt, "delta-zlib", 6)) == 4.67


@pytest.mark.reference
def test_economics():
    e = economics(study()["per_msg"])
    rows = [(r(v["TB_day"]), r(v["PB_year"]), r(v["PB_5y"], 1 if k != "delta columns, zlib 6" else 2),
             round(v["cost"]["total"], -3)) for k, v in e.items()]
    assert rows == [(37.95, 9.56, 47.8, 1989000), (18.97, 4.78, 23.9, 995000), (17.42, 4.39, 21.9, 913000),
                    (3.70, 0.93, 4.67, 194000)]


def test_exercise_arithmetic():
    m = StorageModel(OPRA_MSGS_PER_DAY, 11.9)
    assert r(m.bytes_per_day() / 1e12) == 3.70 and r(m.bytes_per_year() / 1e15) == 0.93
    # exercise 6: five years all in standard storage, per year, at 11.908 bytes a message
    m6 = StorageModel(OPRA_MSGS_PER_DAY, 11.908)
    std = m6.stored_after(5) / 1e9 * PRICES["hot"] * 12
    assert round(std, -3) == 1288000
    assert r(std / 194131, 1) == 6.6


def test_measured_csv_matches_text():
    rows = {x["method"]: x for x in csv.DictReader(open(MEASURED))}
    z6, z9 = float(rows["raw zlib 6"]["mb_per_s"]), float(rows["raw zlib 9"]["mb_per_s"])
    assert z9 < z6 and round(z6 / z9) == 12
    # printed in the solution of exercise 8 (update both after a re-measurement)
    assert (z9, z6, round(float(rows["Parquet zstd 1"]["mb_per_s"]))) == (3.0, 34.5, 220)
    assert r(float(rows["raw zlib 9"]["ratio"]) / float(rows["raw zlib 6"]["ratio"]) - 1, 3) == 0.024
    assert float(rows["Parquet zstd 9"]["mb_per_s"]) > float(rows["norm zlib 6"]["mb_per_s"])
    assert float(rows["Parquet zstd 9"]["ratio"]) > float(rows["norm zlib 6"]["ratio"])
