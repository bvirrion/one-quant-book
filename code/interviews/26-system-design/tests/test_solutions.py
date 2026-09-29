"""Numbers gate for Book 18, chapter 26: the capacity estimates. The matching core is tested in
cpp/iv_book_test.cpp (built by tools/test_code.sh with -Werror) against a brute-force model."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_design import book_memory, feed_bytes_per_day, peak_bits_per_s, risk_updates_per_s, symbols_per_shard


def test_q1_bytes_per_day():
    b = feed_bytes_per_day(200_000, 6.5 * 3600, 64)
    assert round(b / 1e9, 1) == 299.5


def test_q2_peak_bandwidth():
    assert peak_bits_per_s(1_000_000, 64) == 512e6
    assert peak_bits_per_s(1_000_000, 64, overhead_bytes=42) == 848e6  # with Ethernet, IP and UDP headers per message


def test_q5_book_memory():
    b = book_memory(10_000, 5_000_000, 48, 1_000, 16)
    assert b == 240e6 + 320e6 and round(b / 2**20) == 534


def test_q13_risk_updates():
    assert risk_updates_per_s(100_000, 50, 0.01, 1_000) == 50_000_000


def test_q11_shards():
    assert symbols_per_shard(10_000, 3_000_000, 1_000_000, 0.5) == (6, 1667)


def test_worked_answers():
    stages = [1.5, 0.5, 1.0, 3.0, 1.0, 0.5, 2.0]
    assert round(sum(stages), 1) == 9.5 and round(10 - sum(stages), 1) == 0.5
    assert round(100 * (1 - 0.99**7), 1) == 6.8
