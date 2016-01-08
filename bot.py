import logging
import ujson
import re
from aiotg import TgBot
from content.schedule import send_schedule, send_bell
from content.scraper import send_news, send_video
from database import db_check_or_create, db_select
from keyboard import send_keyboard, keyboard, teachers_btns
import settings

logger = logging.getLogger("co1858_bot")

with open("config.json") as cfg:
    config = ujson.load(cfg)

bot = TgBot(**config)


space = r'[\s\-]*'
teachers_re = '|'.join(settings.TEACHERS)
cmds_re = '|'.join(settings.CMDS)
groups_re = r'[0-9]{1,2}' + space + '[абвгклсАБВГКЛС]'
add_space = re.compile('(^[0-9]{1,2})(' + space + ')([абвгклсАБВГКЛС])')
regex = r'/?(({1})|({2})){0}({3})?'.format(
    space, teachers_re, groups_re, cmds_re)


@bot.command(regex)
async def schedule(chat, match):
    logger.debug('%s (%s) %s', chat.sender, chat.sender['id'], match.groups())
    if match.group(2):
        who, cmd = match.group(2, 4)
    if match.group(3):
        who = re.sub(add_space, r'\1 \3', match.group(3))
        cmd = match.group(4)
    await send_schedule(chat, who.capitalize(), cmd)


@bot.command(r'(/menu|/?меню)')
async def menu(chat, match):
    text = 'Выбери пункт меню 👇'
    kb = keyboard()
    await db_check_or_create(**chat.sender)
    await send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'(/teachers|/?учителя)')
async def teachers_menu(chat, match):
    text = '💼 Выбери учителя для просмотра расписания (меню прокручивается)'
    kb = keyboard(teachers_btns())
    await send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'(/groups|/?классы)')
async def groups_menu(chat, match):
    text = '👥 Выбери класс для просмотра расписания (меню прокручивается)'
    kb = keyboard(settings.GROUPS[:])
    await send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'(/bell|/?звонки)')
async def bell(chat, match):
    logger.info('%s: Звонки', chat.sender['id'])
    await send_bell(chat)


@bot.command(r'(/news|/?новости)')
async def news(chat, match):
    logger.info('%s: Новости', chat.sender['id'])
    await send_news(chat)


@bot.command(r'(/video|/?видео)')
async def video(chat, match):
    logger.info('%s: Видео', chat.sender['id'])
    await send_video(chat)


@bot.command(u"\U0001F4F0" + r' (\d{1,2})\. (.*)')
async def news_choose(chat, match):
    logger.info('%s: Новости меню', chat.sender['id'])
    await send_news(chat, int(match.group(1)))


@bot.command(u"\U0001F3A5" + r' (\d{1,2})\. (.*)')
async def video_choose(chat, match):
    logger.info('%s: Видео меню', chat.sender['id'])
    await send_video(chat, int(match.group(1)))


@bot.command(r'/msg (.*)')
async def admin_msg(chat, match):
    if chat.sender['id'] == 133914054:
        subscribed_users = await db_select('msg')
        for chat in subscribed_users:
            logger.info('Админ. сообщение на %s', chat.id)
            await bot.send_message(chat.id, match.group(1))
    else:
        logger.info('Access denied for %s. Echo: %s',
                    chat.sender['id'],
                    match.group(1))
        await chat.reply(match.group(1))


@bot.command(r'(/start)')
async def start(chat, match):
    kb = keyboard()
    await db_check_or_create(**chat.sender)
    await send_keyboard(chat, match.group(1), settings.START_TEXT, kb)


@bot.default
@bot.command(r'(/?help)')
async def usage(chat, match):
    kb = keyboard()
    if isinstance(match, dict):
        chat_text = match['text']
    else:
        chat_text = match.group(1)
    await send_keyboard(chat, chat_text, settings.HELP_TEXT, kb)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)
    bot.run()
