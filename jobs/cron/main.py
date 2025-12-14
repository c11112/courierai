from datetime import datetime
from zoneinfo import ZoneInfo

now = datetime.now(tz=ZoneInfo("UTC"))
print("UTC:", now.isoformat())
print("ET :", now.astimezone(ZoneInfo("America/New_York")).isoformat())
