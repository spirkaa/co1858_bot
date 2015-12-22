import logging
import re
import ujson
from .wday import get_wday
from settings.settings import TEACHERS
from keyboard import keyboard, time_btns

logger = logging.getLogger(__name__)

s_groups = 'content/shedule/s_groups.json'
s_teachers = 'content/shedule/s_teachers.json'

with open(s_groups) as sg, open(s_teachers) as st:
    shedule_groups = ujson.load(sg)
    shedule_teachers = ujson.load(st)


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
    shedule = data['shedule']
    blank = re.compile(r'(\n\d.\s+)*$')
    no_lessons = re.compile(r'^(\d.\s+)+$')
    if re.match(no_lessons, shedule):
        shedule = 'у {} нет уроков в этот день'.format(data['objname'])
    else:
        shedule = re.sub(blank, '', shedule)
    if (not cmd or cmd == 'сегодня'):
        shedule = shedule.replace(current, '*{}* 👈'.format(current))
    result = '{}:\n{}'.format(wday['name'], shedule.lower())
    kb = keyboard(time_btns(who), data['navbtn'])
    logger.info('%s: %s %s', chat.sender['id'], who, cmd)
    logger.debug(repr(result))
    await chat.reply(result, kb, 'Markdown')
