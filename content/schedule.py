import logging
import re
import ujson
from content.wday import get_wday
from keyboard import keyboard, time_btns
from settings import TEACHERS
from storage import get_schedule

logger = logging.getLogger(__name__)


async def send_schedule(chat, redis, who, cmd=None):
    wday = get_wday(cmd)
    lesson_index = wday['lesson']
    data = {}

    async def teacher():
        schedule_teachers = await get_schedule(redis, 'teachers')
        schedule_teachers = ujson.loads(schedule_teachers)
        obj = next(
            v for k, v
            in schedule_teachers.items()
            if k.split(' ')[0] == who)
        data['lesson'] = obj[wday['key']][lesson_index]
        data['objname'] = 'учителя'
        data['schedule'] = '\n'.join(
            ['%s. %s' % (k, v) for (k, v)
             in sorted(obj[wday['key']].items())
             if k != '10' and k != '11'])
        data['navbtn'] = '⬅️ Учителя'
        return

    async def group():
        schedule_groups = await get_schedule(redis, 'groups')
        schedule_groups = ujson.loads(schedule_groups)
        obj = schedule_groups[who.upper()]
        data['lesson'] = ' '.join(obj[wday['key']][lesson_index])
        data['objname'] = 'класса'
        data['schedule'] = '\n'.join(
            ['%s. %s' % (k, ' '.join(v)) for (k, v)
             in sorted(obj[wday['key']].items())])
        data['navbtn'] = '⬅️ Классы'
        return

    try:
        if who in TEACHERS:
            await teacher()
        else:
            await group()
            who = who.upper()
    except RuntimeError as e:
        logger.error(e.args)
        return await chat.reply('отсутствует в БД')
    lesson = data['lesson']
    current = '{}. {}'.format(lesson_index, lesson)
    logger.debug(data)
    schedule = data['schedule']
    blank = re.compile(r'(\n\d.\s+)*$')
    no_lessons = re.compile(r'^(\d.\s+)+$')
    if re.match(no_lessons, schedule):
        schedule = 'у {} нет уроков в этот день'.format(data['objname'])
    else:
        schedule = re.sub(blank, '', schedule)
    if not cmd or cmd == 'сегодня':
        schedule = schedule.replace(current, '*{}* 👈'.format(current))
    result = '{}:\n{}'.format(wday['name'], schedule.lower())
    kb = keyboard(time_btns(who), data['navbtn'])
    await chat.reply(result, kb, 'Markdown')
    logger.info('%s: %s %s', chat.sender['id'], who, cmd)
    logger.debug(repr(result))
