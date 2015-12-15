import logging
import re
import json
from .wday import get_wday
from settings.settings import TEACHERS
from keyboard import keyboard, time_btns

logger = logging.getLogger(__name__)

with open('content/shedule/s_groups.json') as sg:
    shedule_groups = json.load(sg)

with open('content/shedule/s_teachers.json') as st:
    shedule_teachers = json.load(st)


async def send_shedule(chat, who, cmd=None):
    wday = get_wday(cmd)
    lesson_index = wday['lesson']
    data = {}

    def teacher():
        try:
            obj = next(
                v for k, v
                in shedule_teachers.items()
                if k.split(' ')[0] == who)
            data['lesson'] = obj[wday['key']][lesson_index]
            data['objname'] = 'учителя'
            data['shedule'] = '\n'.join(
                ['%s. %s' % (k, v) for (k, v)
                 in sorted(obj[wday['key']].items())
                 if k != '10' and k != '11'])
            data['navbtn'] = '⬅️ Учителя'
        except:
            raise
        return

    def group():
        try:
            obj = shedule_groups[who.upper()]
            data['lesson'] = ' '.join(obj[wday['key']][lesson_index])
            data['objname'] = 'класса'
            data['shedule'] = '\n'.join(
                ['%s. %s' % (k, ' '.join(v)) for (k, v)
                 in sorted(obj[wday['key']].items())])
            data['navbtn'] = '⬅️ Классы'
        except:
            raise
        return

    if who in TEACHERS:
        teacher()
    else:
        group()
        who = who.upper()
    lesson = data['lesson']
    current = '{}. {}'.format(lesson_index, lesson)
    logger.debug(data)
    # расписание на день
    if cmd:
        shedule = data['shedule']
        if cmd == 'сегодня':
            shedule = shedule.replace(current, '*{}*'.format(current))
        no_lessons = re.compile('^(\d.\s+)+$')
        if re.match(no_lessons, shedule):
            shedule = 'у {} нет уроков в этот день'.format(data['objname'])
    # текущий урок
    else:
        cmd = ''
        shedule = current
        if lesson == '' or lesson == ' ':
            shedule = 'у {} нет *{}* урока'.format(data['objname'], lesson_index)
    result = '{}:\n{}'.format(wday['name'], shedule.lower())
    kb = keyboard(time_btns(who), data['navbtn'])
    logger.info('%s: %s %s', chat.sender['id'], who, cmd)
    logger.debug(repr(result))
    await chat.reply(result, kb, 'Markdown')
