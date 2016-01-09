import logging
import os
import re
import ujson
import asyncio
import aioredis
from aiotg import TgBot
from content.bell import send_bell
from content.media import send_news, send_video
from content.schedule import send_schedule
from keyboard import send_keyboard, keyboard, teachers_btns
import storage
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
    who = '5 А'
    cmd = None
    logger.debug('%s (%s) %s', chat.sender, chat.sender['id'], match.groups())
    if match.group(2):
        who, cmd = match.group(2, 4)
    if match.group(3):
        who = re.sub(add_space, r'\1 \3', match.group(3))
        cmd = match.group(4)
    await send_schedule(chat, pool, who.capitalize(), cmd)


@bot.command(r'(/menu|/?меню)')
async def menu(chat, match):
    text = 'Выбери пункт меню 👇'
    kb = keyboard()
    await storage.set_user(pool, **chat.sender)
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
    await send_news(chat, pool)


@bot.command(r'(/video|/?видео)')
async def video(chat, match):
    logger.info('%s: Видео', chat.sender['id'])
    await send_video(chat, pool)


@bot.command(u"\U0001F4F0" + r' (\d{1,2})\. (.*)')
async def news_choose(chat, match):
    logger.info('%s: Новости меню', chat.sender['id'])
    await send_news(chat, pool, int(match.group(1)))


@bot.command(u"\U0001F3A5" + r' (\d{1,2})\. (.*)')
async def video_choose(chat, match):
    logger.info('%s: Видео меню', chat.sender['id'])
    await send_video(chat, pool, int(match.group(1)))


@bot.command(r'/msg (.*)')
async def admin_msg(chat, match):
    if chat.sender['id'] == 133914054:
        subscribed_users = await storage.get_users(pool, 'msg')
        for key in subscribed_users:
            chat_id = int(key)
            logger.info('Админ. сообщение на %s', chat_id)
            await bot.send_message(chat_id, match.group(1))
    else:
        logger.info('Access denied for %s. Echo: %s',
                    chat.sender['id'],
                    match.group(1))
        await chat.reply(match.group(1))


@bot.command(r'(/start)')
async def start(chat, match):
    kb = keyboard()
    await storage.set_user(pool, **chat.sender)
    await send_keyboard(chat, match.group(1), settings.START_TEXT, kb)


@bot.command(r'(/stop)')
async def stop(chat, match):
    logger.info('%s: Стоп', chat.sender['id'])
    await storage.delete_user(pool, **chat.sender)
    await chat.reply('Ваши настройки уведомлений от бота очищены.\nТеперь можете удалить этот чат')


@bot.default
@bot.command(r'(/?help)')
async def usage(chat, match):
    kb = keyboard()
    if isinstance(match, dict):
        chat_text = match['text']
    else:
        chat_text = match.group(1)
    await send_keyboard(chat, chat_text, settings.HELP_TEXT, kb)


async def main():
    global pool
    host = os.environ.get('REDIS_HOST', 'localhost')
    pool = await aioredis.create_pool((host, 6379), encoding="utf-8", minsize=5, maxsize=10)
    await bot.loop()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        bot.stop()
