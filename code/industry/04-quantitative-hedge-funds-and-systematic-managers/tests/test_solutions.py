"""Numbers gate: every numerical answer printed in Book 17, chapter 4 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_quantfunds as q  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "code/firm/formadv"))


def r(x, d=1):
    return round(float(x), d)


def test_summary():
    s = q.summary()
    assert (s["advisers"], s["advisers_10plus"], s["employees_median"]) == (2577, 1458, 11)
    assert [r(s[k]) for k in ("rpe_p25_m", "rpe_p50_m", "rpe_p75_m", "rpe_p90_m")] == [58.3, 119.3, 221.2, 398.6]
    assert [r(100 * s[k], 0) for k in ("adv_share_p25", "adv_share_p50", "adv_share_p75")] == [37, 50, 62]
    assert r(100 * s["gav_top10_share"], 0) == 21 and r(s["gav_hhi"], 0) == 78 and r(s["gav_total_bn"] / 1000) == 17.6


def test_named():
    n = {x["label"]: x for x in q.named()}
    assert len(n) == 13
    rpe = {k: r(v["raum_per_employee_m"]) for k, v in n.items()}
    assert rpe["Squarepoint"] == 2566.6 and rpe["Aspect Capital"] == 24.4 and rpe["Two Sigma Investments"] == 70.0
    assert rpe["Winton Capital Management"] == 69.5 and rpe["PDT Partners"] == 51.9
    assert r(92.0 / 300 * 1000, 0) == 307 and r(100 * 160 / 300, 0) == 53
    inside = sorted(k for k, v in n.items() if 58.3015 <= v["raum_per_employee_m"] <= 221.173)
    assert inside == ["D. E. Shaw & Co.", "Graham Capital Management", "Two Sigma Investments",
                      "Voleon Capital Management", "Winton Capital Management"]
    assert r(n["Winton Capital Management"]["gav_over_raum"], 2) == 0.46 and r(n["AQR Capital Management"]["gav_over_raum"], 2) == 0.55
    assert r(100 * n["Voleon Capital Management"]["advisory_share"], 0) == 16
    assert r(100 * n["AHL Partners (Man Group)"]["advisory_share"], 0) == 81


def test_ranks_and_tail():
    assert r(100 * q.percentile_rank(24.4), 0) == 9 and r(100 * q.percentile_rank(2566.6)) == 99.6
    h = q.hist()
    above = sum(x["advisers"] for x in h if x["log10_lo"] >= 9)
    assert above == 26 and r(100 * above / sum(x["advisers"] for x in h)) == 1.8


def test_hhi_benchmarks():
    import firm_formadv as fa
    assert fa.concentration([1] * 10) == (1.0, 1000.0) or abs(fa.concentration([1] * 10)[1] - 1000) < 1e-6
    assert abs(fa.concentration([1] * 1000)[1] - 10) < 1e-6 and r(10000 / 78, 0) == 128
