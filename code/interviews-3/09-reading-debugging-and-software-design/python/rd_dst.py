from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ny = ZoneInfo("America/New_York")
start = datetime(2026, 3, 8, 0, 0, tzinfo=ny)
end = datetime(2026, 3, 9, 0, 0, tzinfo=ny)
print(end - start)
print(end.astimezone(timezone.utc) - start.astimezone(timezone.utc))
