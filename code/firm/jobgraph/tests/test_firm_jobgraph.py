"""Acceptance tests of firm.jobgraph (One Quant Book 15, chapter 13)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_jobgraph as J  # noqa: E402


def _tasks(ds, **kw):
    return [J.Task(i, d, d, **kw) for i, d in enumerate(ds)]


def test_graham_lpt_example():
    one = J.Cluster(1, 2)
    ts = _tasks([3, 3, 2, 2, 2])
    assert J.simulate(ts, one, J.LPT()).makespan == 7                   # the optimum is 6: 7 <= (4/3 - 1/6) 6
    assert J.lower_bound(ts, 2) == 6
    assert J.simulate(_tasks([1, 1, 1, 1, 4]), one, J.FIFO()).makespan == 6
    assert J.simulate(_tasks([1, 1, 1, 1, 4]), one, J.LPT()).makespan == 4


def test_dependencies_and_chain_bound():
    ts = [J.Task(0, 5, 5), J.Task(1, 5, 5, deps=(0,)), J.Task(2, 1, 1)]
    s = J.simulate(ts, J.Cluster(1, 4), J.FIFO())
    start1 = next(a for tid, _c, a, _b, o in s.runs if tid == 1)
    assert start1 >= s.finish[0] and s.makespan == 10 and J.lower_bound(ts, 4) == 10


def test_fair_share_splits_cores():
    ts = _tasks([10] * 20, team="A") + [J.Task(100 + i, 10, 10, team="B") for i in range(20)]
    s = J.simulate(ts, J.Cluster(1, 4), J.FairShare({"A": 0.5, "B": 0.5}))
    first = [tid for tid, _c, a, _b, _o in s.runs if a == 0]
    assert sum(t < 100 for t in first) == 2 and sum(t >= 100 for t in first) == 2


def test_work_stealing_balances():
    ts = _tasks([10, 1, 1, 1] * 4)                     # dealt round robin: core 0 gets every long task
    pol = J.WorkStealing(4)
    s = J.simulate(ts, J.Cluster(1, 4), pol)
    assert len(s.finish) == 16 and pol.steals > 0 and s.makespan <= 20


def test_speculation_rescues_a_slow_node():
    ts = _tasks([10] * 4)
    cl = J.Cluster(2, 2, slow=(0,), slowdown=5.0)
    plain = J.simulate(ts, cl, J.FIFO())
    spec = J.simulate(ts, cl, J.FIFO(), spec=1.5)
    assert plain.makespan == 50 and spec.makespan == 25 and spec.backups == 2
    assert any(o == "killed" for *_x, o in spec.runs)


def test_failures_are_retried():
    ts = _tasks([3600.0] * 50)
    s = J.simulate(ts, J.Cluster(1, 10, fail_per_hour=0.5, preempt_per_hour=0.5, seed=3), J.FIFO())
    kinds = {o for *_x, o in s.runs}
    assert len(s.finish) == 50 and {"fail", "preempt"} <= kinds and s.wasted > 0


def test_cache_hits_take_no_time():
    cache = {"k"}
    s = J.simulate([J.Task(0, 100, 100, key="k"), J.Task(1, 100, 100, key="j")], J.Cluster(1, 1), J.FIFO(), cache=cache)
    assert s.makespan == 100 and cache == {"k", "j"}


def test_local_executor_and_utilisation():
    order = []
    ts = _tasks([1, 3, 2])
    runs = J.LocalExecutor(J.LPT()).run(ts, {i: (lambda i=i: order.append(i)) for i in range(3)})
    assert order == [1, 2, 0] and [r[0] for r in runs] == [1, 2, 0]
    s = J.simulate(ts, J.Cluster(1, 2), J.FIFO())
    assert J.utilisation(s, [0.5, 2.5, 3.5]) == [2, 2, 0]
