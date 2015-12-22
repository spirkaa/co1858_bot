import logging
import re
import ujson
from aiotg import TgBot
from content.scraper import send_news, send_video
from content.shedule import send_shedule
from settings.settings import CMDS, GROUPS, TEACHERS
from keyboard import send_keyboard, keyboard, teachers_btns

logger = logging.getLogger("co1858_bot")

with open("settings/config.json") as cfg:
    config = ujson.load(cfg)

bot = TgBot(**config)


space = r'[\s\-]*'
teachers_re = ('|').join(TEACHERS)
cmds_re = ('|').join(CMDS)
groups_re = r'[0-9]{1,2}' + space + '[абвгклсАБВГКЛС]'
add_space = re.compile('(^[0-9]{1,2})(' + space + ')([абвгклсАБВГКЛС])')
regex = r'/?(({1})|({2})){0}({3})?'.format(
    space, teachers_re, groups_re, cmds_re)


@bot.command(regex)
def shedule(chat, match):
    logger.debug('%s (%s) %s', chat.sender, chat.sender['id'], match.groups())
    if match.group(2):
        who, cmd = match.group(2, 4)
    if match.group(3):
        who = re.sub(add_space, r'\1 \3', match.group(3))
        cmd = match.group(4)
    return send_shedule(chat, who.capitalize(), cmd)


@bot.command(r'(/menu|/?меню)')
def menu(chat, match):
    text = 'Выбери пункт меню 👇'
    kb = keyboard()
    return send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'(/teachers|/?учителя)')
def teachers_menu(chat, match):
    text = '💼 Выбери учителя для просмотра расписания (меню прокручивается)'
    kb = keyboard(teachers_btns())
    return send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'(/groups|/?классы)')
def groups_menu(chat, match):
    text = '👥 Выбери класс для просмотра расписания (меню прокручивается)'
    kb = keyboard(GROUPS[:])
    return send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'(/bell|/?звонки)')
def bell(chat, match):
    logger.info('%s: Звонки', chat.sender['id'])
    text = """
🔔 Расписание звонков в ЦО № 1858:
1. 08:30 – 09:15\n2. 09:30 – 10:15\n3. 10:30 – 11:20
4. 11:35 – 12:20\n5. 12:40 – 13:25\n6. 13:45 – 14:30
7. 14:50 – 15:35\n8. 15:50 – 16:35\n9. 16:50 – 17:35
    """
    return chat.send_text(text)


@bot.command(r'(/news|/?новости)')
def news(chat, match):
    logger.info('%s: Новости', chat.sender['id'])
    return send_news(chat)


@bot.command(r'(/video|/?видео)')
def video(chat, match):
    logger.info('%s: Видео', chat.sender['id'])
    return send_video(chat)


@bot.command(u"\U0001F4F0" + r' (\d{1,2})\. (.*)')
def news_choose(chat, match):
    logger.info('%s: Новости меню', chat.sender['id'])
    return send_news(chat, int(match.group(1)))


@bot.command(u"\U0001F3A5" + r' (\d{1,2})\. (.*)')
def video_choose(chat, match):
    logger.info('%s: Видео меню', chat.sender['id'])
    return send_video(chat, int(match.group(1)))


@bot.default
@bot.command(r'(/start|/?help)')
def usage(chat, match):
    text = """
⭐ Привет! Я знаю всё о расписании Центра образования № 1858.

📅 Чтобы посмотреть расписание, отправь мне название класса или фамилию учителя:
11 а завтра
Лазарева четверг

👇 А лучше просто воспользуйся меню 👇

/teachers - 💼 список учителей
/groups - 👥 список классов
/bell - 🔔 расписание звонков

💬 Ошибки, предложения и пожелания: @spirkaa
    """
    kb = keyboard()
    if isinstance(match, dict):
        logtext = match['text']
    else:
        logtext = match.group(1)
    return send_keyboard(chat, logtext, text, kb)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.INFO)
    bot.run()
