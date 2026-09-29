"""firm.fibreroute -- long-haul fibre routes as spans, their latency by component, and their cost (build of One Quant
Book 14, chapter 13).

A route is a chain of spans between two sites of firm.geomap. Each span has a length of glass, a group index, an
optical amplifier at its end (a few metres of doped fibre and a pass-through time) and optionally a spool of
dispersion-compensating fibre; the route's two terminals add transponder and forward-error-correction time. The
latency splits into: glass along the geodesic, extra path, dispersion compensation, amplifiers and terminals.
All equipment times are parameters of the model, stated where used, not measurements of any product.

API (stable):
    Span(km, n_g=1.462, amp_us=0.1, dcf_km=0.0)
    Route(name, geodesic_km, spans, terminal_us=0.0)
    build(name, geodesic_km, factor, span_km=80.0, n_g=1.462, amp_us=0.1, dcf_frac=0.0, terminal_us=0.0) -> Route
    components(route) -> dict(glass, path, dcf, amps, terminals, total)             one-way microseconds
    invert(published_us, geodesic_km, n_g=1.462, equipment_us=0.0) -> dict(path_km, factor, excess_km)
    with_index(route, n_g) -> Route                                                  same path, another glass
    Costs: dark(iru, years, om_year, capex, capex_years) ; lit(monthly) -> annual ; break_even_years(...)
"""
from dataclasses import dataclass, replace

C0 = 299_792_458.0


def _us(km, n):
    return km * 1e3 * n / C0 * 1e6


@dataclass(frozen=True)
class Span:
    km: float
    n_g: float = 1.462
    amp_us: float = 0.1
    dcf_km: float = 0.0


@dataclass(frozen=True)
class Route:
    name: str
    geodesic_km: float
    spans: tuple
    terminal_us: float = 0.0

    @property
    def km(self):
        return sum(s.km for s in self.spans)


def build(name, geodesic_km, factor, span_km=80.0, n_g=1.462, amp_us=0.1, dcf_frac=0.0, terminal_us=0.0):
    """A route whose glass is `factor` times the geodesic, cut into spans of at most span_km."""
    if factor < 1:
        raise ValueError("a fibre path cannot be shorter than the geodesic")
    total = geodesic_km * factor
    n = max(1, int(-(-total // span_km)))
    per = total / n
    spans = tuple(Span(per, n_g, amp_us, per * dcf_frac) for _ in range(n))
    return Route(name, geodesic_km, spans, terminal_us)


def components(route):
    n = route.spans[0].n_g
    glass = _us(route.geodesic_km, n)
    path = sum(_us(s.km, s.n_g) for s in route.spans) - glass
    dcf = sum(_us(s.dcf_km, s.n_g) for s in route.spans)
    amps = sum(s.amp_us for s in route.spans)
    term = 2 * route.terminal_us
    return {"glass": glass, "path": path, "dcf": dcf, "amps": amps, "terminals": term,
            "total": glass + path + dcf + amps + term}


def invert(published_us, geodesic_km, n_g=1.462, equipment_us=0.0):
    """A published one-way latency, less assumed equipment time, as the glass the route must have."""
    glass_us = published_us - equipment_us
    path_km = glass_us * 1e-6 * C0 / n_g / 1e3
    return {"path_km": path_km, "factor": path_km / geodesic_km,
            "excess_km": path_km - geodesic_km}


def with_index(route, n_g):
    return replace(route, spans=tuple(replace(s, n_g=n_g) for s in route.spans))


def dark(iru, years, om_year, capex, capex_years):
    """Annual cost of dark fibre: the IRU over its term, O&M, and the firm's own
    optical equipment over its life."""
    return iru / years + om_year + capex / capex_years


def lit(monthly):
    return 12 * monthly


def break_even_years(iru, om_year, capex, monthly):
    """Years after which dark fibre (IRU and equipment up front, O&M yearly) has cost less
    in total than a lit service at `monthly`; infinite if the lease is always cheaper."""
    saving = 12 * monthly - om_year
    return float("inf") if saving <= 0 else (iru + capex) / saving
