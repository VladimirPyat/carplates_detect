from datetime import datetime


def get_date(date_format='%m.%d.%Y'):
    return datetime.now().strftime(date_format)


def get_time(time_format='%H:%M:%S'):
    return datetime.now().strftime(time_format)
