from datetime import datetime


def midpoint_date(date1: datetime, date2: datetime) -> datetime:
    return date1 + (date2 - date1) / 2
