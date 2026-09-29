"""firm.teamtopo -- services, their dependencies and incidents, and how the teams that own them are drawn (build of One
Quant Book 16, chapter 21). Graph code by hand.

A design assigns every service to one team and every engineer to one team. Coordination cost: for each dependency
a -> b whose two services belong to different teams, the change frequency of b (each change to b needs the owners
of a to be told, tested with and scheduled). On-call load: each team's pages a week (the sum of its services'
incident rates) spread over its engineers. Bus factor of a service: the number of engineers who can operate it (its
owning team's members plus named backups); the design's bus factor is the smallest over its services, and the
services at that minimum are the ones that one or two departures would orphan.

API (stable):
    Service(name, change_per_week, pages_per_week) ; Design(owner, team_size, backups)
    cross_edges(deps, design) ; coordination(services, deps, design) ; pages(services, design) -> {team: per engineer}
    bus_factor(services, design) -> (minimum, services at the minimum) ; move(design, from_team, to_team)
    report(services, deps, design) -> dict
"""
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Service:
    name: str
    change_per_week: float
    pages_per_week: float


@dataclass(frozen=True)
class Design:
    owner: dict                          # service name -> team
    team_size: dict                      # team -> engineers
    backups: dict = field(default_factory=dict)   # service name -> engineers outside the team who can operate it


def cross_edges(deps, design):
    return [(a, b) for a, b in deps if design.owner[a] != design.owner[b]]


def coordination(services, deps, design):
    freq = {s.name: s.change_per_week for s in services}
    return sum(freq[b] for _, b in cross_edges(deps, design))


def pages(services, design):
    load = {t: 0.0 for t in design.team_size}
    for s in services:
        load[design.owner[s.name]] += s.pages_per_week
    return {t: load[t] / design.team_size[t] for t in design.team_size}


def bus_factor(services, design):
    bf = {s.name: design.team_size[design.owner[s.name]] + design.backups.get(s.name, 0) for s in services}
    low = min(bf.values())
    return low, sorted(k for k, v in bf.items() if v == low)


def move(design, from_team, to_team):
    """One engineer moves between teams."""
    sizes = dict(design.team_size)
    sizes[from_team] -= 1
    sizes[to_team] += 1
    return replace(design, team_size=sizes)


def report(services, deps, design):
    p = pages(services, design)
    eng = sum(design.team_size.values())
    total_pages = sum(s.pages_per_week for s in services)
    bf, weakest = bus_factor(services, design)
    return {"cross_edges": len(cross_edges(deps, design)), "coordination": coordination(services, deps, design),
            "pages_max": max(p.values()), "pages_mean": total_pages / eng, "bus_factor": bf, "weakest": weakest,
            "teams": len(design.team_size)}
