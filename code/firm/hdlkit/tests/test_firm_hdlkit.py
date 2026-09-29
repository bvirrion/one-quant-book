"""Both simulators, the golden model and each other, on random frames with random back-pressure. The tests fail,
never skip, if Verilator or Icarus is missing (firm_hdlkit.ToolMissing)."""
import functools
import pathlib
import random
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_hdlkit as h  # noqa: E402

THRESH = 0x8000_0000


def frames(seed, n=30):
    rng = random.Random(seed)
    return [bytes(rng.randrange(256) for _ in range(rng.randrange(8, 90))) for _ in range(n)]


@functools.lru_cache
def sims(tmp, pipe):
    d = pathlib.Path(tmp)
    return (h.build_verilator(d / f"v{pipe}", {"OFF": 6, "LEN": 4, "PIPE": pipe}),
            h.build_icarus(d, {"OFF": 6, "LEN": 4, "PIPE": pipe}))


@pytest.fixture(scope="module")
def tmp(tmp_path_factory):
    return str(tmp_path_factory.mktemp("hdk"))


def test_tools_are_installed():
    h.require("verilator", "iverilog", "vvp")          # fails loudly: the book's HDL chapters depend on them


@pytest.mark.parametrize("pipe", [0, 1])
def test_both_simulators_match_the_golden_model_under_backpressure(tmp, pipe):
    v, i = sims(tmp, pipe)
    d = pathlib.Path(tmp)
    for seed in range(3):
        fr = frames(seed)
        h.write_stim(d / "s.txt", fr, idle_every=3 + seed)
        rng = random.Random(100 + seed)
        h.write_ready(d / "r.txt", [rng.random() < 0.7 for _ in range(97)])
        a = h.run_verilator(v, d / "s.txt", d / "r.txt", THRESH)
        b = h.run_icarus(i, d / "s.txt", d / "r.txt", THRESH)
        assert a == b                                              # cycle for cycle
        ev, g = h.events(a), h.golden(fr, 6, 4, THRESH)
        assert [x for _, x in ev["F"]] == g["F"] and [x for _, x in ev["C"]] == g["C"]
        assert [x for _, x in ev["M"]] == g["M"]
        assert len(ev["I"]) == sum(len(h.beats(f)) for f in fr)   # every beat accepted once


def test_latency_in_cycles(tmp):
    """Without back-pressure: the skid buffer registers the completing beat at the edge that accepts it; the field is
    registered at the next edge; the comparison PIPE + 1 edges after that."""
    d = pathlib.Path(tmp)
    fr = [bytes(range(16))]
    h.write_stim(d / "s1.txt", fr)
    h.write_ready(d / "r1.txt", [1])
    for pipe in (0, 1):
        ev = h.events(h.run_verilator(sims(tmp, pipe)[0], d / "s1.txt", d / "r1.txt", THRESH))
        accept_beat1 = ev["I"][1]                                    # bytes 8-15 complete the field (bytes 6-9)
        assert ev["F"][0][0] - accept_beat1 == 1
        assert ev["M"][0][0] - ev["F"][0][0] == pipe + 1
        assert ev["F"][0][1] == int.from_bytes(bytes([6, 7, 8, 9]), "big")


def test_beats_and_golden_by_hand():
    assert h.beats(bytes(range(10))) == [(0, 0xFF, 0x0001020304050607), (1, 0xC0, 0x0809000000000000)]
    g = h.golden([bytes(range(12))], 6, 4, 0x06070809)
    assert g["F"] == [0x06070809] and g["M"] == [1]
