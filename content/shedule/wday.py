import logging
from collections import OrderedDict
from datetime import datetime, time, timedelta

logger = logging.getLogger(__name__)


def get_lesson_num(now):
    intervals = OrderedDict([
        (0, [0, 0, 7, 0]),
        (1, [7, 0, 9, 15]),
        (2, [9, 15, 10, 15]),
        (3, [10, 15, 11, 20]),
        (4, [11, 20, 12, 20]),
        (5, [12, 20, 13, 25]),
        (6, [13, 25, 14, 30]),
        (7, [14, 30, 15, 35]),
        (8, [15, 35, 16, 35]),
        (9, [16, 35, 17, 35]),
        (10, [17, 35, 0, 0]),
        ])
    for k, v in intervals.items():
        if time(v[0], v[1]) <= now.time() <= time(v[2], v[3]):
            return k
    return 10


def get_wday(cmd=None):
    now = datetime.now()
    wday_index = now.weekday()
    tommorow = now + timedelta(days=1)
    tomorrow_index = tommorow.weekday()
    lesson_num = get_lesson_num(now)
    week = {
        0: {'key': 'mon', 'name': 'понедельник', 'slug': 'пн'},
        1: {'key': 'tue', 'name': 'вторник', 'slug': 'вт'},
        2: {'key': 'wed', 'name': 'среда', 'slug': 'ср'},
        3: {'key': 'thu', 'name': 'четверг', 'slug': 'чт'},
        4: {'key': 'fri', 'name': 'пятница', 'slug': 'пт'},
        5: {'key': 'sat', 'name': 'суббота', 'slug': 'сб'},
        6: {'key': 'sun', 'name': 'воскресенье', 'slug': 'вс'}}
    wday = week[wday_index]
    today_header = 'сегодня, {}, 📅 {}'.format(
        wday['name'], datetime.strftime(now, '%d.%m.%Y'))
    # если в запросе cmd - расписание на день cmd
    if (cmd and cmd != 'завтра'):
        if cmd == 'сегодня':
            wday['name'] = today_header
        for k, day in week.items():
            for key, value in day.items():
                if value == cmd:
                    wday = week[k]
        wday['lesson'] = str(lesson_num)
    # во внеурочное время текущего дня - расписание на завтра
    elif (cmd == 'завтра' or lesson_num == 10):
        wday = week[tomorrow_index]
        wday['name'] = 'завтра, {}, 📅 {}'.format(
            wday['name'], datetime.strftime(tommorow, '%d.%m.%Y'))
        wday['lesson'] = str(1)
    elif lesson_num == 0:
        wday['name'] = today_header
        wday['lesson'] = str(1)
    # по умолчанию - текущий урок
    else:
        wday['lesson'] = str(lesson_num)
        wday['name'] = 'сейчас, 🕒 {}'.format(datetime.strftime(now, '%H:%M'))
    # в выходные - расписание на понедельник
    if (wday['key'] == 'sat' or wday['key'] == 'sun'):
        wday = week[0]
        wday['name'] = 'следующий рабочий день - ' + wday['name']
        wday['lesson'] = str(1)
    logger.debug(wday)
    return wday
