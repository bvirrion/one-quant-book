"""Derive the chapter's small tables from one SEC Form ADV adviser file (run once; the raw file is not committed).

    .venv/bin/python in_adv_derive.py /path/to/ia010226.zip

Writes data/industry/adv_hedge_summary.csv (distribution statistics of hedge-fund advisers) and
data/industry/adv_named.csv (the named managers' rows), and the histogram behind the chapter's figure.
"""
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/formadv"))
import firm_formadv as fa  # noqa: E402

NAMED = {  # legal name pattern -> (label, category, ledger row of chapter 4)
    r"^RENAISSANCE TECHNOLOGIES LLC$": ("Renaissance Technologies", "systematic", "F7"),
    r"^TWO SIGMA INVESTMENTS, LP$": ("Two Sigma Investments", "systematic", "F8"),
    r"^TWO SIGMA ADVISERS, LP$": ("Two Sigma Advisers", "systematic", "F8"),
    r"^AQR CAPITAL MANAGEMENT, LLC$": ("AQR Capital Management", "systematic", "F9"),
    r"^AHL PARTNERS LLP$": ("AHL Partners (Man Group)", "systematic", "F10"),
    r"^WINTON CAPITAL MANAGEMENT LTD\.$": ("Winton Capital Management", "systematic", "F11"),
    r"^ASPECT CAPITAL LIMITED$": ("Aspect Capital", "systematic", "F12"),
    r"^CAPITAL FUND MANAGEMENT S\.A\.$": ("Capital Fund Management", "systematic", "F13"),
    r"^SQUAREPOINT OPS LLC$": ("Squarepoint", "systematic", "F14"),
    r"^PDT PARTNERS, LLC$": ("PDT Partners", "systematic", "F15"),
    r"^VOLEON CAPITAL MANAGEMENT LP$": ("Voleon Capital Management", "systematic", "F16"),
    r"^D\. E\. SHAW & CO\., L\.P\.$": ("D. E. Shaw & Co.", "systematic and discretionary", "F17"),
    r"^GRAHAM CAPITAL MANAGEMENT, L\.P\.$": ("Graham Capital Management", "systematic and discretionary", "F18"),
}


def main(src):
    advs = fa.read(src)
    big = [a for a in advs if a.employees and a.employees >= 10 and a.raum]
    rpe = [fa.per_head(a)["raum_per_employee"] for a in big]
    share = [fa.per_head(a)["advisory_share"] for a in big]
    top10, hhi = fa.concentration([a.pf_gav for a in advs], 10)
    q = fa.quantiles(rpe, (0.1, 0.25, 0.5, 0.75, 0.9))
    s = fa.quantiles(share, (0.25, 0.5, 0.75))
    out = ROOT / "data/industry"
    with open(out / "adv_hedge_summary.csv", "w") as f:
        f.write("stat,value\n")
        stats = dict(advisers=len(advs), advisers_10plus=len(big), gav_total_bn=sum(a.pf_gav or 0 for a in advs) / 1e9,
                     gav_top10_share=top10, gav_hhi=hhi, rpe_p10_m=q[0] / 1e6, rpe_p25_m=q[1] / 1e6,
                     rpe_p50_m=q[2] / 1e6, rpe_p75_m=q[3] / 1e6, rpe_p90_m=q[4] / 1e6, adv_share_p25=s[0],
                     adv_share_p50=s[1], adv_share_p75=s[2], employees_median=fa.quantiles(
                         [a.employees for a in advs], (0.5,))[0])
        for k, v in stats.items():
            f.write(f"{k},{v:.6g}\n")
    with open(out / "adv_named.csv", "w") as f:
        f.write("label,category,employees,advisory,raum_bn,pf_gav_bn,n_hedge,filed,ledger\n")
        for a in advs:
            for pat, (lab, cat, led) in NAMED.items():
                if re.match(pat, a.name):
                    f.write(f"{lab},{cat},{a.employees:.0f},{a.advisory:.0f},{a.raum / 1e9:.2f},"
                            f"{(a.pf_gav or 0) / 1e9:.2f},{a.n_hedge:.0f},{a.filed},{led}\n")
    edges = [x / 4 for x in range(20, 45)]  # log10 of RAUM per employee, $100k to $10bn
    counts = [0] * (len(edges) - 1)
    for v in rpe:
        lv = math.log10(v)
        for i in range(len(counts)):
            if edges[i] <= lv < edges[i + 1]:
                counts[i] += 1
    with open(out / "adv_rpe_hist.csv", "w") as f:
        f.write("log10_lo,log10_hi,advisers\n")
        for i, c in enumerate(counts):
            f.write(f"{edges[i]:.2f},{edges[i + 1]:.2f},{c}\n")


if __name__ == "__main__":
    main(sys.argv[1])
