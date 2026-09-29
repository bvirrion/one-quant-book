"""firm.venuesites -- which venue matches where (build of One Quant Book 14, chapter 11).

A registry from venue (by ISO 10383 MIC) to the sites of firm.geomap: its primary data centre, secondary or
disaster-recovery site, points of presence (pop) and market-data distribution points (md). Every row names the
ledger rows that source it and the date it was read; a row may carry the dates between which it held (a venue's
migration is two rows). Book 1's firm.venues registry is joined through a wrapper, never edited.

API (stable):
    ROLES
    VenueSite(mic, venue, role, site, valid_from, valid_to, source, as_of)    dates "YYYY-MM-DD" or ""
    Registry.load(path=DATA, sites_path=SITES)       rows and the site table (firm.geomap sites)
    Registry.rows(mic=None, role=None, on=None)      rows, optionally for one venue, role and date
    Registry.primary(mic, on=None) -> site id        the venue's primary site on a date (error if none or several)
    Registry.venues_at(site_id, on=None) -> [mic]    the venues whose primary site it is
    Registry.nearest(from_site, role="primary", on=None, medium="vacuum")
                                                     [(mic, site, km, floor_us)] sorted by distance
    Registry.moves(mic) -> [(date, old_site, new_site)]    migrations recorded in the table
    Registry.stale(today, days=90) -> [row]           rows read more than `days` ago
    join_venues(registry, venues) -> [(Venue, VenueSite)]  with Book 1's firm.venues Registry, primary rows only

Rule on dates: an empty valid_from means the source gives no start date, and the row says nothing about earlier dates;
an empty valid_to means the row still holds as of `as_of`.
"""
import csv
import datetime as dt
import pathlib
import sys
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "geomap"))
import firm_geomap as gm  # noqa: E402

DATA = HERE / "data" / "venue_sites.csv"
SITES = ROOT / "data" / "networks" / "sites.csv"
ROLES = ("primary", "secondary", "dr", "pop", "md")


@dataclass(frozen=True)
class VenueSite:
    mic: str
    venue: str
    role: str
    site: str
    valid_from: str
    valid_to: str
    source: str
    as_of: str

    def holds_on(self, on):
        if on is None:
            return not self.valid_to
        started = not self.valid_from or self.valid_from <= on
        return started and (not self.valid_to or on <= self.valid_to)


class Registry:
    def __init__(self, rows, sites):
        self.sites = {s.id: s for s in sites}
        for r in rows:
            if r.role not in ROLES:
                raise ValueError(f"{r.mic}: unknown role {r.role!r}")
            if r.site not in self.sites:
                raise ValueError(f"{r.mic}: site {r.site!r} is not in the site table")
            if not r.source or not r.as_of:
                raise ValueError(f"{r.mic}: a row needs its source and the date it was read")
            if r.valid_from and r.valid_to and r.valid_from > r.valid_to:
                raise ValueError(f"{r.mic}: valid_from after valid_to")
        self._rows = list(rows)

    @classmethod
    def load(cls, path=DATA, sites_path=SITES):
        with open(path, newline="", encoding="utf8") as f:
            rows = [VenueSite(**r) for r in csv.DictReader(f)]
        return cls(rows, gm.load_sites(sites_path))

    def rows(self, mic=None, role=None, on=None):
        keep = [r for r in self._rows if mic is None or r.mic == mic]
        return [r for r in keep if (role is None or r.role == role) and r.holds_on(on)]

    def primary(self, mic, on=None):
        found = {r.site for r in self.rows(mic, "primary", on)}
        if len(found) != 1:
            raise LookupError(f"{mic} on {on or 'today'}: {len(found)} primary sites")
        return found.pop()

    def venues_at(self, site_id, on=None):
        return sorted({r.mic for r in self.rows(role="primary", on=on) if r.site == site_id})

    def nearest(self, from_site, role="primary", on=None, medium="vacuum"):
        a = self.sites[from_site]
        out = []
        for r in self.rows(role=role, on=on):
            b = self.sites[r.site]
            d = gm.geodesic_m(a.lat, a.lon, b.lat, b.lon)
            out.append((r.mic, r.site, d / 1e3, gm.floor_us(d, medium)))
        return sorted(out, key=lambda x: (x[2], x[0]))

    def moves(self, mic):
        mine = [r for r in self._rows if r.mic == mic and r.role == "primary"]
        out = []
        for r in sorted((r for r in mine if r.valid_from), key=lambda r: r.valid_from):
            before = [p for p in mine if p.valid_to and p.valid_to < r.valid_from]
            if before:
                out.append((r.valid_from, max(before, key=lambda p: p.valid_to).site, r.site))
        return out

    def stale(self, today, days=90):
        t = dt.date.fromisoformat(today)
        return [r for r in self._rows if (t - dt.date.fromisoformat(r.as_of)).days > days]


def join_venues(registry, venues):
    """Pairs (firm.venues.Venue, VenueSite) for the MICs present in both registries, current primary rows."""
    out = []
    for r in registry.rows(role="primary"):
        try:
            out.append((venues.get(r.mic), r))
        except KeyError:
            continue
    return out
