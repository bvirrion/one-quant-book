"""firm.serverspec -- choosing trading servers (build of One Quant Book 14, chapter 8).

A hot path's time splits into a part that scales with the core's clock (instructions, cache hits) and a part that
does not (memory, the card, the bus). With a share phi of core-bound time measured at a reference clock f_ref,
    t(f) = t_ref * (phi * f_ref / f + 1 - phi).
Candidate processors and servers are data, each row naming its ledger source; a cabinet holds as many servers as its
power and its rack units allow. The firmware settings of chapter 8 are audited into firm.tuneaudit Findings, so that
one report covers the host (Book 13, chapter 13) and its firmware.

API (stable):
    Candidate(name, cores, base_ghz, hot_ghz, cache_mb, tdp_w, sockets, server_w, rack_u, source)
        hot_ghz: the clock the hot core runs at (single-core boost, or a vendor's all-core figure)
    CANDIDATES                                      the chapter's table (dated rows; see the ledger)
    path_ns(t_ref_ns, phi, f_ghz, f_ref_ghz)        the latency model
    speedup(phi, f_ghz, f_ref_ghz)
    per_cabinet(c, cabinet_kw, cabinet_u=42)        servers that fit by power and by space
    rank(t_ref_ns, phi, f_ref_ghz, cabinet_kw)      candidates by predicted latency, with servers and cores per cabinet
    FIRMWARE                                        the settings checklist: name -> wanted value
    firmware_audit(settings) -> list[firm_tuneaudit.Finding]
"""
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tuneaudit"))
import firm_tuneaudit as ta  # noqa: E402


@dataclass(frozen=True)
class Candidate:
    name: str
    cores: int
    base_ghz: float
    hot_ghz: float
    cache_mb: float
    tdp_w: float
    sockets: int
    server_w: float          # whole-server power budgeted per server: sockets x TDP + 250 W, or a vendor's figure
    rack_u: int
    source: str


def _std(name, cores, base, hot, cache, tdp, src, sockets=1, u=1):
    return Candidate(name, cores, base, hot, cache, tdp, sockets, sockets * tdp + 250.0, u, src)


CANDIDATES = (
    _std("AMD EPYC 9175F", 16, 4.2, 5.0, 512, 320, "F3"),
    _std("Intel Xeon Gold 6544Y", 16, 3.6, 4.1, 45, 270, "F4"),
    _std("AMD EPYC 9755", 128, 2.7, 4.1, 512, 500, "F3", sockets=2, u=2),
    Candidate("overclocked Xeon w7-2495X server", 24, 4.8, 4.8, 45, 0.0, 1, 2000.0, 2, "F5"),
)


def speedup(phi, f_ghz, f_ref_ghz):
    return 1.0 / (phi * f_ref_ghz / f_ghz + 1.0 - phi)


def path_ns(t_ref_ns, phi, f_ghz, f_ref_ghz):
    return t_ref_ns * (phi * f_ref_ghz / f_ghz + 1.0 - phi)


def per_cabinet(c, cabinet_kw, cabinet_u=42):
    by_power = int(cabinet_kw * 1000 // c.server_w)
    by_space = cabinet_u // c.rack_u
    return min(by_power, by_space)


def rank(t_ref_ns, phi, f_ref_ghz, cabinet_kw):
    rows = []
    for c in CANDIDATES:
        n = per_cabinet(c, cabinet_kw)
        rows.append({"name": c.name, "hot_ghz": c.hot_ghz, "path_ns": path_ns(t_ref_ns, phi, c.hot_ghz, f_ref_ghz),
                     "servers": n, "cores": n * c.cores * c.sockets})
    return sorted(rows, key=lambda r: r["path_ns"])


FIRMWARE = {"power_profile": "maximum performance", "cstates": "disabled", "smt": "disabled on hot cores",
            "turbo": "enabled, fixed", "smi_sources": "minimised (vendor-approved)", "memory_speed": "maximum rated",
            "numa_interleave": "disabled", "edac": "lowest functional level", "sriov": "disabled"}


def firmware_audit(settings):
    out = []
    for k, want in FIRMWARE.items():
        got = settings.get(k)
        status = "unknown" if got is None else ("ok" if got == want else "fail")
        out.append(ta.Finding(f"firmware:{k}", status, f"want {want}, found {got}"))
    return out
