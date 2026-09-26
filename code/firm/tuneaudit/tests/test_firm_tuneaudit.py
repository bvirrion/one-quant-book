import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "coreplan"))
import firm_coreplan as cp  # noqa: E402
import firm_tuneaudit as ta  # noqa: E402

DATA = HERE / "data"
PLAN = cp.plan(cp.read_topology(HERE.parent / "coreplan/data/two_socket"), "ens1f0")


def test_plan_is_the_one_the_fixtures_describe():
    assert sorted(PLAN.roles[r] for r in ("feed", "strategy", "gateway")) == [21, 22, 23]
    assert PLAN.idle == (29, 30, 31)


def test_helpers():
    assert ta.mask_cpus("0000ffff") == set(range(16))
    assert ta.mask_cpus("00000000,00000003") == {0, 1}
    assert ta.selected("always [madvise] never") == "madvise"
    assert ta.cmdline_params("quiet isolcpus=1-3") == {"quiet": "", "isolcpus": "1-3"}


def test_tuned_host_passes_every_rule():
    f = ta.audit(DATA / "tuned", PLAN)
    assert [x.rule for x in f] == list(ta.RULES)
    assert all(x.status == "ok" for x in f), ta.report(f)


def test_mistuned_host_reports_each_mistake():
    f = {x.rule: x for x in ta.audit(DATA / "mistuned", PLAN)}
    fails = {r for r, x in f.items() if x.status == "fail"}
    assert fails == {"siblings", "nohz_full", "rcu_nocbs", "irq_affinity", "irqbalance", "governor", "cstate", "thp",
                     "memlock"}
    assert f["isolated"].status == "ok"
    assert f["siblings"].detail.endswith("29,30,31")
    assert f["irq_affinity"].detail.endswith("default, 120")
    assert f["governor"].detail == "CPU 22: powersave"
    assert "903" in f["irqbalance"].detail


def test_real_time_threads_need_throttling_off():
    f = {x.rule: x for x in ta.audit(DATA / "tuned", PLAN, fifo=True)}
    assert f["rt_throttle"].status == "fail" and "950000" in f["rt_throttle"].detail


def test_a_bigger_lock_requirement_fails_the_mistuned_limit_only():
    need = 128 << 20
    assert {x.rule for x in ta.failures(ta.audit(DATA / "tuned", PLAN, memlock_bytes=need))} == set()
    assert "memlock" in {x.rule for x in ta.failures(ta.audit(DATA / "mistuned", PLAN, memlock_bytes=need))}


def test_unexposed_settings_are_unknown_not_ok(tmp_path):
    f = {x.rule: x for x in ta.audit(tmp_path, PLAN)}
    assert f["governor"].status == "unknown" and f["thp"].status == "unknown" and f["memlock"].status == "unknown"
    assert f["isolated"].status == "fail"
