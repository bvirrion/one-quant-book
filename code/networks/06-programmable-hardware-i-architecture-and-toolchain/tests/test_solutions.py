"""Numbers gate: every number printed in Book 14, chapter 6 (text and solutions); HDL runs fail if a simulator is
missing."""
import pathlib
import random
import sys
import zlib

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_fpga as f  # noqa: E402

h = f.h


def test_clocks_and_timing_model():
    assert f.clock_mhz(10, 64) == 156.25 and f.clock_mhz(25, 64) == 390.625
    assert f.clock_mhz(25, 32) == 781.25 and f.clock_mhz(25, 128) == 195.3125
    t1, t3 = f.timing(12, 1), f.timing(12, 3)
    assert (t1["period_ns"], t1["fmax_mhz"], t1["latency_ns"]) == (pytest.approx(6.4), pytest.approx(156.25), pytest.approx(6.4))
    assert round(t3["fmax_mhz"], 1) == 416.7 and t3["period_ns"] == pytest.approx(2.4)
    assert f.depth_for(12, 390.625) == 3 and f.depth_for(12, 156.25) == 1 and f.depth_for(12, 195.3125) == 2
    assert f.timing(12, 5)["fmax_mhz"] == f.timing(12, 4)["fmax_mhz"] and round(f.timing(12, 6)["fmax_mhz"]) == 714
    assert round(1e3 / 390.625, 2) == 2.56 and round(3 * 2.56, 2) == 7.68 and round(2 * 1e3 / 195.3125, 2) == 10.24
    assert round(f.timing(12, 2)["fmax_mhz"]) == 294
    assert 16 * 6.4 == pytest.approx(102.4) and 16 * 2.56 == pytest.approx(40.96)
    assert 9 * 2.56 == pytest.approx(23.04) and round(40.96 - 23.04, 1) == 17.9


def test_first_frame_table(tmp_path):
    for pipe, cmp_cycle in ((0, 3), (1, 4)):
        ev = f.first_frame(tmp_path / f"p{pipe}", pipe)
        assert ev["I"] == [0, 1] and ev["F"] == [(2, 0x16171819)] and ev["C"] == [(2, zlib.crc32(f.FRAME))]
        assert ev["M"] == [(cmp_cycle, 1)]
    assert f"{zlib.crc32(f.FRAME):08x}" == "f4a7fd67"


def test_field_at_other_offsets(tmp_path):
    """Exercises 3 and 7: fields ending in a later beat appear a cycle later; offset 10, length 8 in both simulators."""
    fr = bytes(range(24))
    for off, length, beat in ((12, 4, 1), (14, 4, 2), (10, 8, 2)):
        exe = h.build_verilator(tmp_path / f"v{off}", {"OFF": off, "LEN": length, "PIPE": 1})
        h.write_stim(tmp_path / "s.txt", [fr])
        h.write_ready(tmp_path / "r.txt", [1])
        ev = h.events(h.run_verilator(exe, tmp_path / "s.txt", tmp_path / "r.txt", 0))
        assert ev["F"][0] == (ev["I"][beat] + 1, int.from_bytes(fr[off:off + length], "big"))
    rng = random.Random(7)
    frames = [bytes(rng.randrange(256) for _ in range(rng.randrange(18, 60))) for _ in range(12)]
    vv = h.build_verilator(tmp_path / "v7", {"OFF": 10, "LEN": 8, "PIPE": 1})
    iv = h.build_icarus(tmp_path, {"OFF": 10, "LEN": 8, "PIPE": 1})
    h.write_stim(tmp_path / "s7.txt", frames, idle_every=4)
    h.write_ready(tmp_path / "r7.txt", [rng.random() < 0.6 for _ in range(31)])
    a = h.run_verilator(vv, tmp_path / "s7.txt", tmp_path / "r7.txt", 1 << 63)
    b = h.run_icarus(iv, tmp_path / "s7.txt", tmp_path / "r7.txt", 1 << 63)
    assert a == b and [x for _, x in h.events(a)["F"]] == h.golden(frames, 10, 8, 1 << 63)["F"]
