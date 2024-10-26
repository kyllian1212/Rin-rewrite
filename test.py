from datetime import datetime, date, time
from zoneinfo import ZoneInfo
looptime = time(hour=3, tzinfo=ZoneInfo("America/Los_Angeles")) 
dt = datetime.combine(date.today(), looptime)
print(dt, round(dt.timestamp()))