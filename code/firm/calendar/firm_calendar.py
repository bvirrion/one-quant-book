"""Global contract calendar (build of Book 1, Chapter 22): which futures are open, in UTC.

Sessions are given in the exchange's local time and may cross midnight; daylight saving is handled
by the time-zone database, which is the whole reason this module exists. Holidays are not handled:
a production calendar loads them from each exchange.
"""
import csv
import datetime as dt
from dataclasses import dataclass
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc


@dataclass(frozen=True)
class Session:
    root: str
    tz: str
    open: dt.time
    close: dt.time                  # if close <= open the session ends on the next local day
    first_day: int                  # weekday of the first session OPEN of the week, Monday = 0
    last_day: int                   # weekday of the last session OPEN of the week

    def opens_on(self, weekday: int) -> bool:
        if self.first_day <= self.last_day:
            return self.first_day <= weekday <= self.last_day
        return weekday >= self.first_day or weekday <= self.last_day

    def interval(self, local_date: dt.date) -> tuple[dt.datetime, dt.datetime] | None:
        """UTC interval of the session that opens on `local_date`, or None."""
        if not self.opens_on(local_date.weekday()):
            return None
        zone = ZoneInfo(self.tz)
        start = dt.datetime.combine(local_date, self.open, zone)
        end_date = local_date if self.close > self.open else local_date + dt.timedelta(days=1)
        end = dt.datetime.combine(end_date, self.close, zone)
        return start.astimezone(UTC), end.astimezone(UTC)


def load(path: str) -> list[Session]:
    out = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            a, b = (int(x) for x in r["days"].split("-"))
            out.append(Session(r["root"], r["timezone"], dt.time.fromisoformat(r["open"]),
                               dt.time.fromisoformat(r["close"]), a, b))
    return out


def is_open(sessions: list[Session], root: str, when: dt.datetime) -> bool:
    when = when.astimezone(UTC)
    for s in sessions:
        if s.root != root:
            continue
        local = when.astimezone(ZoneInfo(s.tz)).date()
        for d in (local - dt.timedelta(days=1), local):
            iv = s.interval(d)
            if iv and iv[0] <= when < iv[1]:
                return True
    return False


def open_roots(sessions: list[Session], when: dt.datetime) -> list[str]:
    return sorted({s.root for s in sessions if is_open(sessions, s.root, when)})


def utc_intervals(sessions: list[Session], root: str, day: dt.date) -> list[tuple[dt.datetime, dt.datetime]]:
    """All UTC intervals of `root` that intersect the UTC day `day`, clipped to it."""
    lo = dt.datetime.combine(day, dt.time(0), UTC)
    hi = lo + dt.timedelta(days=1)
    out = []
    for s in sessions:
        if s.root != root:
            continue
        for k in (-2, -1, 0, 1):
            iv = s.interval(day + dt.timedelta(days=k))
            if iv and iv[0] < hi and iv[1] > lo:
                out.append((max(iv[0], lo), min(iv[1], hi)))
    return sorted(set(out))
