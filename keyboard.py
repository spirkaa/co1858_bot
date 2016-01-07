import logging
import ujson
import textwrap
from settings.settings import TEACHERS
from database import db_check_or_create

logger = logging.getLogger(__name__)


def time_btns(who):
    buttons = [['сегодня', 'завтра'],
               ['пн', 'вт'],
               ['ср', 'чт'],
               ['пт']]
    for row in buttons:
        row[:] = [(who + ' ' + item) for item in row[:]]
    return buttons


def teachers_btns():
    tlist = sorted(TEACHERS)
    return [[one, two] for one, two in zip(tlist[0::2], tlist[1::2])]


def scraper_btns(block, spec, icon):
    buttons = []
    for index, v in enumerate(block[1:]):
        if spec == 'news':
            title = v.select_one('.h3').text
        elif spec == 'video':
            title = v.select_one('a').attrs.get('title')
        buttons.append(['{} {}. {}'.format(
            icon,
            index+1,
            textwrap.shorten(title, width=25, placeholder='…'))])
    return buttons


def keyboard(buttons=None, navbtn='⬅️ Меню'):
    if buttons:
        buttons.insert(0, [navbtn])
        buttons.append([navbtn])
    else:
        buttons = [['💼 Учителя'],
                   ['👥 Классы'],
                   ['🔔 Звонки'],
                   ['📰 Новости ЦО', '🎥 Видео ЦО']]
    return {"keyboard": buttons, "resize_keyboard": True}


async def send_keyboard(chat, command, text, kb):
    logger.info('%s: %s', chat.sender['id'], command)
    await chat.send_text(text, reply_markup=ujson.dumps(kb))
