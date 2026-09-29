"""firm.colobill -- colocation and connectivity bills from published fee schedules (build of One Quant Book 14, ch. 9).

A schedule is a venue's published fees as data: each item has a monthly fee, a one-time fee, the ledger row that
sources it and the date it was read. A footprint is a list of (item, quantity). The bill is monthly recurring fees
plus one-time fees amortised over a term; items older than a staleness limit are flagged, because fee schedules
change by filing (chapter 9's dated boxes).

API (stable):
    Item(name, monthly, one_time, unit, source, as_of)          as_of: "YYYY-MM-DD" of the ledger row
    Schedule(venue, currency, items)                             items: {key: Item}
    SCHEDULES                                                    the chapter's two published schedules
    bill(schedule, footprint, term_months=36) -> dict(monthly, one_time, amortised, total_monthly, annual, lines)
    stale(schedule, today, days=60) -> [key]
    break_even(total_monthly, units_per_month) -> float          cost per unit traded that the footprint must earn
    equalisation_ns(own_m, longest_m, n_g=1.462) -> float        delay a coil adds to a nearer cabinet
"""
import datetime as dt
from dataclasses import dataclass

C0 = 299_792_458.0


@dataclass(frozen=True)
class Item:
    name: str
    monthly: float
    one_time: float
    unit: str
    source: str
    as_of: str


@dataclass(frozen=True)
class Schedule:
    venue: str
    currency: str
    items: dict


SCHEDULES = {
    "nasdaq-ny11-4": Schedule("Nasdaq, NY11-4 (Carteret)", "USD", {
        "uhd_cabinet": Item("Ultra High Density Cabinet (10-15 kW)", 7_230.0, 0.0, "cabinet", "F3", "2026-09-28"),
        "cabinet_install": Item("Cabinet installation (NY11-4)", 0.0, 5_940.0, "cabinet", "F3", "2026-09-28"),
        "power_install_p3": Item("Phase 3 cabinet power installation", 0.0, 4_560.0, "cabinet", "F3", "2026-09-28"),
        "pdu_p3": Item("Phase 3 power distribution unit (optional)", 0.0, 5_260.0, "cabinet", "F3", "2026-09-28"),
    }),
    "miax-pearl": Schedule("MIAX Pearl Options", "USD", {
        "ull_10g": Item("10Gb ultra-low-latency connection, primary/secondary", 15_000.0, 0.0, "connection", "F5",
                        "2026-09-28"),
        "dr_10g": Item("10Gb connection, disaster recovery facility", 3_500.0, 0.0, "connection", "F5", "2026-09-28"),
        "conn_1g": Item("1Gb connection, primary/secondary", 1_500.0, 0.0, "connection", "F5", "2026-09-28"),
    }),
}


def bill(schedule, footprint, term_months=36):
    lines, monthly, one_time = [], 0.0, 0.0
    for key, qty in footprint:
        it = schedule.items[key]
        lines.append((it.name, qty, qty * it.monthly, qty * it.one_time))
        monthly += qty * it.monthly
        one_time += qty * it.one_time
    amort = one_time / term_months
    return {"monthly": monthly, "one_time": one_time, "amortised": amort, "total_monthly": monthly + amort,
            "annual": 12 * (monthly + amort), "lines": lines}


def stale(schedule, today, days=60):
    t = dt.date.fromisoformat(today)
    return [k for k, it in schedule.items.items() if (t - dt.date.fromisoformat(it.as_of)).days > days]


def break_even(total_monthly, units_per_month):
    return total_monthly / units_per_month


def equalisation_ns(own_m, longest_m, n_g=1.462):
    return max(0.0, longest_m - own_m) * n_g / C0 * 1e9
