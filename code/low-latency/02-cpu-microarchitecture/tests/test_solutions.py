"""Numbers gate, Book 13 chapter 2. Measured figures are checked against the committed CSVs with the tolerance the
text's wording allows ("about"); exact arithmetic is checked exactly."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_cpu as c  # noqa: E402


def near(x, want, rel=0.2):
    return abs(x - want) <= rel * abs(want)


def test_exercises_exact():
    assert 600 * 4.0 * 2.4 == 5760                          # 1
    assert 3000 / 3.0 == 1000 and 1000 * 4.5 == 4500        # 2
    assert c.chains_needed(4, 2) == 8 and 3 / 8 == 0.375    # 3
    assert c.branch_cost(0, 0.3, 20) == 6.0                 # 4: 6 cycles against 4
    assert c.chains_needed(2, 2) == 4                       # text: four chains


def test_measured_branch():
    b = c.branch()
    assert near(b[("branchy", "sorted")], 0.21, 0.05) and near(b[("branchless", "sorted")], 0.32, 0.05)
    assert near(b[("branchy", "shuffled")], 2.80, 0.05) and near(b[("branchless", "shuffled")], 0.32, 0.05)
    assert round(b[("branchy", "shuffled")] / b[("branchy", "sorted")]) == 13          # about thirteen times
    ns, cyc = c.penalty()
    assert round(ns, 1) == 5.2 and round(cyc) == 24 and round(c.clock_ghz(), 2) == 4.64
    assert round(b[("branchless", "sorted")] - b[("branchy", "sorted")], 2) == 0.11
    assert near(c.break_even(), 0.021, 0.4)                                          # about two in a hundred
    # problem 7 and 8, at the committed figures
    assert b[("branchy", "sorted")] + 0.01 * ns < b[("branchless", "sorted")]        # quiet day: branchy wins
    assert round(b[("branchy", "sorted")] + 0.35 * ns - b[("branchless", "shuffled")], 1) == 1.7
    assert round(50_000 * 0.35 * 5.2 / 1000) == 91                                   # us per second


def test_measured_chains_and_clock():
    k = c.chains()
    assert near(k[1] / k[2], 2, 0.15) and near(k[2] / k[4], 2, 0.15)
    assert near(k[8], k[4], 0.1) and near(k[16], k[4], 0.15)
    lo, hi, med, imm = c.freq_summary()
    assert 2.0 < lo <= med <= hi < 5.0 and 4 < imm <= 6.5                            # about five, up to six
    blocks = {int(x["block"]): float(x["ns_per_element"]) for x in c._rows("measured_blocks.csv")}
    base = c.branch()[("branchy", "sorted")]
    assert all(blocks[bb] < 1.5 * base for bb in (1, 2, 4, 8, 1024))                 # exercise 7: learnt
    assert blocks[16] > 1.8 * base
