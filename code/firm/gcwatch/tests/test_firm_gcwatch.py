import collections
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_gcwatch as g


def test_pooled_loop_causes_no_collection():
    pool = g.RecordPool(1024)

    def step(k):
        i = pool.next()
        pool.buf["ts"][i] = k
        pool.buf["price"][i] = 1_000_000 + k % 7
        pool.buf["qty"][i] = 100

    r = g.steady_state(step, 50_000)
    assert r["collections"] == {0: 0, 1: 0, 2: 0}
    assert pool.buf["ts"][pool.i] == 1000 + 50_000 - 1


def test_bounded_churn_triggers_nothing_but_growth_does():
    # CPython counts tracked allocations minus deallocations: a bounded live set never reaches the threshold
    keep = collections.deque(maxlen=1000)
    r = g.steady_state(lambda k: keep.append({"id": k, "fills": [k]}), 50_000)
    assert r["collections"] == {0: 0, 1: 0, 2: 0}
    book = {}

    def step(k):                       # an order book that fills up: two orders added for one removed
        book[k] = {"id": k, "px": 100 + k % 7, "fills": [k]}
        if k % 2 == 0 and k - 500 in book:
            del book[k - 500]

    r = g.steady_state(step, 50_000)
    assert r["collections"][0] > 50 and r["pauses"].pauses[0].count == r["collections"][0]
