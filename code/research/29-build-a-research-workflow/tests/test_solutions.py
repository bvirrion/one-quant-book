"""Numbers gate: every numerical answer printed in Book 7, chapter 29 (text and solutions)."""
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_workflow import always_in_universe, make, never_in_universe, tearsheet_v2

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "researchlog"))
from firm_researchlog import ResearchLog  # noqa: E402
from firm_workflow import diff, register, reproduce  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def ran(m):
    return [n for n, s in m["stages"].items() if s["ran"]]


def test_reference_study_and_scenarios():
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as e, tempfile.TemporaryDirectory() as f:
        out, m = make()(d).run()
        c, t = out["cards"], out["tearsheet"]
        assert (r(c["momentum"]["ic"], 4), r(c["momentum"]["t"]), r(c["reversal"]["ic"], 4), r(c["reversal"]["t"]), c["reversal"]["days"]) == \
            (0.0076, 1.39, 0.0379, 16.05, 2267)
        assert (r(t["sr"]), r(t["se_iid"]), r(t["lo"]), r(t["hi"]), r(100 * t["turnover"], 1)) == (0.08, 0.33, -0.67, 0.74, 3.5)
        assert len(m["stages"]) == 8 and ran(make()(d).run()[1]) == []
        pa, da = never_in_universe(d)
        _, ma = make(revisions=[(da, pa, 0.5)])(d).run()
        assert ran(ma) == ["snapshot", "universe", "features", "cards", "level1"]
        assert diff(m, ma) == {"snapshot": ["params", "output"], "universe": ["inputs"], "features": ["inputs"], "cards": ["inputs"],
                               "level1": ["inputs"]}
        pb, db = always_in_universe(d)
        _, mb = make(revisions=[(db, pb, 0.5)])(d).run()
        assert len(ran(mb)) == 8 and set(diff(m, mb)) == set(m["stages"])
        _, mc = make(weights={"momentum": 0.7, "reversal": 0.3})(d).run()
        assert ran(mc) == ["blend", "portfolio", "level1", "tearsheet"]
        _, md = make(tear=tearsheet_v2)(d).run()
        assert ran(md) == ["tearsheet"] and diff(m, md) == {"tearsheet": ["code", "output"]}
        assert reproduce(make(), m, e) == []
        _, mu = make(seed=None)(d).run()
        assert reproduce(make(seed=None), mu, f) == ["tearsheet"]
        log = ResearchLog()
        log.register("reference", "momentum and reversal blended monthly earn a positive Sharpe ratio", "2026-09-25T09:00:00")
        entry = register(m, log, "reference", "2026-09-25T10:00:00", {"sr": t["sr"]})
        assert log.trial_count("reference") == 1 and entry.body["data_id"] == m["stages"]["snapshot"]["output"]
        assert (pa, da, pb, db) == (13, 5, 4, 1000)
