import logging
import ujson
from settings import TEACHERS, ADMINS

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
    buttons = [[one, two] for one, two in zip(tlist[0::2], tlist[1::2])]
    if len(TEACHERS) % 2 != 0:
        buttons.append([TEACHERS[-1]])
    return buttons


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
        buttons = [['💼 Учителя', '👥 Классы', '🔔 Звонки'],
                   ['📰 Новости ЦО', '🎥 Видео ЦО'],
                   ['🔧Настройки', '❓Помощь'],
                   ]
    return {"keyboard": buttons, "resize_keyboard": True}


async def send_keyboard(chat, command, text, kb):
    logger.info('%s (%s): %s', chat.sender['id'], chat.sender['first_name'], command)
    if chat.sender['id'] in ADMINS:
        kb['keyboard'].append(['🅰️ Админ'])
    await chat.send_text(text, reply_markup=ujson.dumps(kb))
