"""Numbers gate for Book 18, chapter 25: interleaving explorers (exact under sequential consistency), systems
arithmetic, gap detection against an oracle, and ThreadSanitizer runs: the race snippet must be diagnosed (its
output is never asserted), the SPSC queue must run clean. cpp/iv_spsc_test.cpp is also built with -Werror by
tools/test_code.sh."""
import pathlib
import platform
import random
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_conc import (
    MESSAGE_PASSING,
    STORE_BUFFERING,
    counter_final_values,
    gaps,
    page_table_levels,
    sc_outcomes,
    tlb_reach,
)

CPP = pathlib.Path(__file__).resolve().parents[1] / "cpp"


def test_q5_lost_updates():
    assert min(counter_final_values(1)) == 1
    for n in (2, 3, 4):
        assert min(counter_final_values(n)) == 2 and max(counter_final_values(n)) == 2 * n


def test_q6_store_buffering():
    out = {tuple(v for _, v in o) for o in sc_outcomes(*STORE_BUFFERING)}
    assert out == {(0, 1), (1, 0), (1, 1)}  # (0, 0) impossible under sequential consistency


def test_q7_message_passing():
    out = {tuple(v for _, v in o) for o in sc_outcomes(*MESSAGE_PASSING)}
    assert (1, 0) not in out and out == {(0, 0), (0, 1), (1, 1)}


def test_q8_false_sharing():
    assert 64 // 8 == 8  # eight int64 counters share one 64-byte line


def test_q9_pages():
    assert page_table_levels() == (4, 9, 12)
    assert 4 * 9 + 12 == 48
    assert tlb_reach(1536, 4096) == 6 * 2**20 and tlb_reach(1536, 2**21) == 3 * 2**30


def test_q12_gaps():
    assert gaps([1, 2, 3, 6, 7, 5, 10]) == [(4, 4), (8, 9)]
    for s in range(300):
        r = random.Random(s)
        full = list(range(1, r.randint(2, 40)))
        kept = [x for x in full if r.random() > 0.2] or [1]
        stream = kept[:]
        for _ in range(r.randint(0, 3)):  # late re-deliveries
            i = r.randrange(len(stream))
            stream.insert(i + r.randint(1, 3), stream[i])
        got = gaps(stream)
        missing = [x for x in range(kept[0], max(kept) + 1) if x not in set(stream)]
        flat = [x for a, b in got for x in range(a, b + 1)]
        assert flat == missing


def run_tsan(src, tmp_path, extra=()):
    exe = tmp_path / "prog"
    subprocess.run(["g++", "-std=c++20", "-O1", "-g", "-fsanitize=thread", *extra, str(src), "-o", str(exe)],
                   check=True, capture_output=True)
    r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=300)
    # ThreadSanitizer versus high-entropy ASLR: it either reports an unexpected memory mapping or dies at start-up
    # with a signal and no output; either way, run again without ASLR.
    if "unexpected memory mapping" in r.stderr or r.returncode < 0:
        r = subprocess.run(["setarch", platform.machine(), "-R", str(exe)], capture_output=True, text=True, timeout=300)
    return r


def test_q1_q5_race_is_diagnosed(tmp_path):
    r = run_tsan(CPP / "snippets" / "race_counter.cpp", tmp_path)
    assert "ThreadSanitizer: data race" in r.stderr


def test_q10_spsc_is_race_free(tmp_path):
    r = run_tsan(CPP / "iv_spsc_test.cpp", tmp_path, ("-I", str(CPP)))
    assert r.returncode == 0 and "ThreadSanitizer" not in r.stderr and "all passed" in r.stdout


def test_worked_answers():
    assert round(200_000 * 15e-6, 9) == 3
    assert 10**6 - 2 * 10**5 == 800_000 and round(1024 / 800_000 * 1e3, 2) == 1.28
    assert 10**6 * 64 == 64 * 10**6
    rnd = random.Random(25)
    t, area, last = 0.0, 0.0, 0.0
    events = []
    for _ in range(50_000):
        t += rnd.expovariate(200_000)
        events.append((t, 1))
        events.append((t + rnd.expovariate(1 / 15e-6), -1))
    events.sort()
    n = 0
    for time, d in events:
        area += n * (time - last)
        last = time
        n += d
    assert abs(area / last - 3) < 0.15
