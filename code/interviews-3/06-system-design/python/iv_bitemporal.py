"""Two times per row: when the event happened, and when we came to know this version of it."""


class Bitemporal:
    def __init__(self):
        self.rows = []

    def insert(self, event_time, known_time, value):
        self.rows.append((event_time, known_time, value))

    def as_of(self, known_at):
        """The table at known_at: for each event, the latest version known by then."""
        best = {}
        for event_time, known_time, value in self.rows:
            if known_time <= known_at:
                if event_time not in best or known_time >= best[event_time][0]:
                    best[event_time] = (known_time, value)
        return {event: version[1] for event, version in sorted(best.items())}
