
from datetime import datetime, time
from dateutil.tz import *
import pytz

tz = pytz.timezone("EST")

usTime = datetime.now(tz).time()
print(usTime)

timeStr = "12:10:59"


timeNew = datetime.strptime(timeStr, "%H:%M:%S")


# timeNew = timeNew.replace(tzinfo=tz)


timeDetal = usTime - timeNew


spanSeconds = timeDetal.total_seconds()
print(spanSeconds)

