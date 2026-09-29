"""firm.edupipe -- counting the degrees that feed the industry (build of One Quant Book 17, chapter 29).

The US completions survey (IPEDS, table C{year}_A) reports awards by institution, programme code (CIP), first or
second major and award level; this module streams one year's file from its zip and totals awards for chosen codes and
levels, first majors only, so that a degree is counted once. A placement report is a programme's own account of its
graduates' jobs: the record keeps the cohort, how many sought work, how many accepted offers, how many reported pay,
the reported median and the report's own caveats, so that a reader sees the response behind each figure.

API (stable):
    LEVELS ; read_ipeds(zip_path, cips, levels) -> {(cip, level): awards}
    PlacementReport(programme, cohort, students, seeking, accepted, reporting, median_base, standard, note)
        .placement_rate ; .reporting_rate ; .median_quantile_bounds() -> the quantiles of the reported pay between which
        the median of all job-seekers lies whatever the non-reporters earn
"""
import csv
import io
import zipfile
from dataclasses import dataclass

LEVELS = {"3": "associate", "5": "bachelor", "7": "master", "17": "doctorate (research)"}


def read_ipeds(zip_path, cips, levels=tuple(LEVELS)):
    """Awards by (CIP code, award level) for first majors, from an IPEDS completions zip (C{year}_A)."""
    cips, levels = set(cips), {str(int(x)) for x in levels}
    out = {}
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as f:
            for row in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1")):
                d = {k.strip().upper().lstrip("\ufeff").lstrip("\u00ef\u00bb\u00bf"): v for k, v in row.items() if k}
                cip = d["CIPCODE"].strip().strip('"')
                lvl = str(int(d["AWLEVEL"].strip()))
                if cip in cips and lvl in levels and d.get("MAJORNUM", "1").strip() == "1":
                    out[(cip, lvl)] = out.get((cip, lvl), 0) + int(d["CTOTALT"] or 0)
    return out


@dataclass(frozen=True)
class PlacementReport:
    programme: str
    cohort: str
    students: int | None
    seeking: int
    accepted: int
    reporting: int | None      # graduates reporting pay; None when the report does not say
    median_base: float
    standard: str              # the reporting standard the report follows, if any
    note: str = ""

    @property
    def placement_rate(self):
        return self.accepted / self.seeking

    @property
    def reporting_rate(self):
        return None if self.reporting is None else self.reporting / self.accepted

    def median_quantile_bounds(self):
        """The median of all `accepted` lies between these quantiles of the reported pay distribution, whatever the
        non-reporters earn (all below, or all above, the reporters)."""
        if self.reporting is None:
            return None
        k = self.accepted - self.reporting
        half = self.accepted / 2.0
        return max(0.0, (half - k) / self.reporting), min(1.0, half / self.reporting)
