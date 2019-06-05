import datetime
import logging
import urllib.request, urllib.error
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def is_holiday():
    day = datetime.date.today()
    today = day.strftime("%Y%m%d")

    url = 'https://calendar.google.com/calendar/ical/ja.japanese%23holiday%40group.v.calendar.google.com/public/basic.ics'
    try:
        response = urllib.request.urlopen(url=url)
        list = response.readlines()
    except Exception as e:
        logger.error(e)
        return False

    for num in range(len(list)):
        pattern = r"(?:DTSTART;VALUE=DATE:)([0-9]{8})"
        repatter = re.compile(pattern)
        match = repatter.match(list[num-1].decode('utf-8'))
        if match:
            if today == match.group(1):
                logger.info("today is holiday:" + match.group(1))
                return True

    logger.info("today is not holiday")

    return False
