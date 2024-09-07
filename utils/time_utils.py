from datetime import datetime, timedelta

DATEFORMAT = '%m.%d.%Y'
TIMEFORMAT = '%H:%M:%S'


def get_date(date_format=DATEFORMAT):
    return datetime.now().strftime(date_format)


def get_time(time_format=TIMEFORMAT):
    return datetime.now().strftime(time_format)


def is_timeout(date_string, time_string, timeout):
    # получаем из лога время в виде строки и задаем таймаут в секундах
    now = datetime.now()
    time_delta = timedelta(seconds=timeout)
    checked_time = datetime.strptime(f'{date_string} {time_string}', f'{DATEFORMAT} {TIMEFORMAT}')
    # если разница между временными отметками меньше таймаута - возвращаем true

    if now - checked_time < time_delta:
        return True

    return False
