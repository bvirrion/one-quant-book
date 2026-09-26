import os
import pathlib
import sys
from dataclasses import replace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_venueprofile as vp  # noqa: E402


def test_validate_rules():
    reg = vp.standard()
    assert len(reg) == 11 and len(reg.simulated()) == 8
    assert all(vp.validate(p) == [] for p in reg)
    crypto, event, fx = reg.get("crypto"), reg.get("event"), reg.get("fx_ecn")
    assert any("not paced" in e for e in vp.validate(replace(crypto, quoting=vp.HOME)))
    assert any("0.250" in e for e in vp.validate(replace(crypto, quoting=replace(vp.HOME, gap_ns=8 * 10**9))))
    assert any("multiple of the lot" in e for e in vp.validate(replace(fx, quoting=vp.HOME)))
    assert any("does not offer" in e for e in vp.validate(replace(event, quoting=replace(vp.HOME, post_only=True))))
    odd = replace(reg.get("lit"), mic="xl", matching="batch", top_pct=10, speed_bump_ns=0, asymmetric=True)
    errs = vp.validate(odd)
    assert len(errs) == 5       # MIC, top_pct, batch without interval, asymmetric without delay, post-only unused


def test_registry_roundtrip_and_records(tmp_path):
    reg = vp.standard()
    reg.dump(tmp_path / "venues.json")
    back = vp.Registry.load(tmp_path / "venues.json")
    assert [p for p in back] == [p for p in reg]
    fut = reg.get("futures_pr")
    cfg = vp.exchange_config(fut)
    inst = cfg.instruments[0]
    assert inst.matching == "configurable" and inst.alloc["top_pct"] == 40 and inst.tick == 2500 and inst.lot == 1
    assert vp.exchange_config(reg.get("batch")).batch_interval_ns == 100_000_000
    ev = vp.exchange_config(reg.get("event"))
    assert ev.speed_bump_ns == 5 * 10**9 and ev.asymmetric_delay
    assert vp.exchange_config(reg.get("crypto")).fees.unit == "bp"
    assert vp.venue_record(fut).fee_model == "per_contract"
    assert vp.fee_schedule(reg.get("inverted")).daily_bill(1000, 1000, 1e6) == 1000 * 0.0010 - 1000 * 0.0005
    try:
        vp.exchange_config(reg.get("on_chain"))
        raise AssertionError("an on-chain venue has no matching engine to simulate")
    except ValueError:
        pass
    j = vp.jumps(600)
    assert 15 <= len(j) <= 50 and {s for _, s in j} <= {-1, 1}


def test_runs_show_the_venue_rules():
    reg = vp.standard()
    lit = vp.run(reg.get("lit"), seconds=300)
    bump = vp.run(reg.get("bump"), seconds=300)
    assert lit["picked"] > 0 and bump["picked"] == lit["picked"]          # a symmetric delay changes no race here
    inv = vp.run(reg.get("inverted"), seconds=300)
    assert inv["volume"] == lit["volume"] and inv["fees_ticks"] > 0 > lit["fees_ticks"]
    ev = vp.run(reg.get("event"), vp.HOME, seconds=300)
    assert ev["picked"] < lit["picked"]                                    # the cancel beats the delayed taker
    home = vp.run(reg.get("crypto"), vp.HOME, seconds=300)
    own = vp.run(reg.get("crypto"), seconds=300)
    assert home["rejects"] > 0.5 * home["orders"] and own["rejects"] == 0 and own["messages"] < home["messages"]
    big = vp.run(reg.get("futures_pr"), seconds=300)
    small = vp.run(reg.get("futures_pr"), vp.HOME, seconds=300)
    assert big["volume"] > 2 * small["volume"]
