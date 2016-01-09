import logging
import ujson
from settings import TEACHERS

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


def scraper_btns(block, icon):
    buttons = []
    for item in block[1:]:
        buttons.append(['{} {}'.format(icon, item)])
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
