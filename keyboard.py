import logging
import json
import textwrap
from settings.settings import TEACHERS

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
    buttons = []
    tlist = sorted(TEACHERS)
    for one, two in zip(tlist[0::2], tlist[1::2]):
        buttons.append([one, two])
    return buttons


def scraper_btns(block, spec, icon):
    buttons = []
    for k, v in enumerate(block[1:]):
        if spec == 'news':
            data = v.select_one('.h3').text
        elif spec == 'video':
            data = v.select_one('a').attrs.get('title')
        buttons.append(['{} {}. {}'.format(
            icon,
            k+1,
            textwrap.shorten(data, width=25, placeholder='…'))])
    return buttons


def keyboard(buttons=None, navbtn='⬅️ Меню'):
    if buttons:
        buttons.insert(0, [navbtn])
        buttons.append([navbtn])
    else:
        buttons = [['💼 Учителя'],
                   ['👥 Классы'],
                   ['🔔 Звонки'],
                   ['📰 Новости', '🎥 Видео']]
    return {"keyboard": buttons, "resize_keyboard": True}


async def send_keyboard(chat, command, text, kb):
    logger.info('%s: %s', chat.sender['id'], command)
    await chat.send_text(text, reply_markup=json.dumps(kb))
