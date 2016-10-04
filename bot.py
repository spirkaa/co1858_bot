import logging
import os
import re
import asyncio
import aioredis
from aiotg import Bot
from content.bell import send_bell
from content.media import send_news, send_video
from content.schedule import send_schedule
from keyboard import send_keyboard, keyboard, teachers_btns
import storage
import settings

logger = logging.getLogger("co1858_bot")

bot = Bot(
    api_token=os.environ.get("API_TOKEN"),
    name=os.environ.get("BOT_NAME"),
    botan_token=os.environ.get("BOTAN_TOKEN"))

# content commands: schedule
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


@bot.command(r'/?(teachers|учителя)')
async def teachers_menu(chat, match):
    text = 'Расписание учителей пока не работает'
    await chat.reply(text)

# async def teachers_menu(chat, match):
#     text = '💼 Выбери учителя для просмотра расписания (меню прокручивается)'
#     kb = keyboard(teachers_btns())
#     await send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'/?(groups|классы)')
async def groups_menu(chat, match):
    text = '👥 Выбери класс для просмотра расписания (меню прокручивается)'
    kb = keyboard(settings.GROUPS[:])
    await send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'/?(bell|звонки)')
async def bell(chat, match):
    logger.info('%s: Звонки', chat.sender['id'])
    await send_bell(chat)


# content commands: media
E_NEWS = u'\U0001F4F0'  # 📰
E_VIDEO = u'\U0001F3A5'  # 🎥
media_re = r'\s(\d{1,2})\.\s+(.*)'


@bot.command(r'^({}+\s/?(news|новости))'.format(E_NEWS))
async def news(chat, match):
    logger.info('%s: Новости', chat.sender['id'])
    await send_news(chat, pool)


@bot.command(r'^{}+{}'.format(E_NEWS, media_re))
async def news_choose(chat, match):
    num = int(match.group(1))
    logger.info('%s: Новости меню, %s', chat.sender['id'], num)
    await send_news(chat, pool, num)


@bot.command(r'^({}+\s/?(video|видео))'.format(E_VIDEO))
async def video(chat, match):
    logger.info('%s: Видео', chat.sender['id'])
    await send_video(chat, pool)


@bot.command(r'^{}+{}'.format(E_VIDEO, media_re))
async def video_choose(chat, match):
    num = int(match.group(1))
    logger.info('%s: Видео меню, %s', chat.sender['id'], num)
    await send_video(chat, pool, num)


# User settings commands
E_CHECK = u'\U00002714'  # ✔
E_CROSS = u'\U0000274C'  # ❌


@bot.command(r'/?(settings|настройки)')
async def user_config(chat, match):
    logger.info('%s: Настройки', chat.sender['id'])
    user = await storage.get_user(pool, chat.sender['id'])
    actions = {}
    for k, v in user.items():
        if k in settings.SUBS.values():
            if v == '1':
                actions[k] = E_CHECK
                actions[k + '_action'] = E_CROSS + ' отписаться'
            else:
                actions[k] = E_CROSS
                actions[k + '_action'] = E_CHECK + ' подписаться'
    logger.debug('settings %s', actions)
    text = settings.USER_CFG.format(**actions)
    news_btn = 'Новости: {}'.format(actions['sub_news_action'])
    video_btn = 'Видео: {}'.format(actions['sub_video_action'])
    msg_btn = 'Сообщения: {}'.format(actions['sub_msg_action'])
    btns = [[news_btn], [video_btn], [msg_btn]]
    kb = keyboard(btns)
    await send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'^(видео|новости|сообщения):\s([{}{}])'.format(E_CHECK, E_CROSS))
async def set_cfg(chat, match):
    val = '0'
    key = settings.SUBS[match.group(1).lower()]
    if match.group(2) == E_CHECK:
        val = '1'
    await storage.update_user(pool, chat.sender['id'], key, val)
    await user_config(chat, match)


# Admin commands


@bot.command(r'/?(admin|админ)')
async def admin(chat, match):
    if chat.sender['id'] in settings.ADMINS:
        buttons = [['/dbstat', '/users']]
        kb = keyboard(buttons)
        await send_keyboard(chat, match.group(1), settings.ADMIN_TEXT, kb)
    else:
        await chat.send_text(settings.HELP_TEXT)


@bot.command(r'/msg (.*)')
async def admin_msg(chat, match):
    if chat.sender['id'] in settings.ADMINS:
        subscribed_users = await storage.get_users_sub(pool, 'msg')
        msg_title = '*сообщение для всех от* @spirkaa:'
        msg_footer = 'Настроить уведомления от бота:\n/settings'
        text = '{}\n{}\n---\n{}'
        text = text.format(msg_title, match.group(1), msg_footer)
        md = {'parse_mode': 'Markdown'}
        for key in subscribed_users:
            chat_id = int(key)
            logger.info('%s %s', msg_title, chat_id)
            try:
                await bot.send_message(chat_id, text, **md)
            except RuntimeError:
                await storage.delete_user(pool, key)
    else:
        logger.info('Доступ запрещен. %s: %s',
                    chat.sender['id'],
                    match.group(1))
        await chat.reply(match.group(1))


@bot.command(r'/users( stat)?')
async def admin_users(chat, match):
    if chat.sender['id'] in settings.ADMINS:
        logger.debug('admin_users, %s', chat.sender['id'])
        users = await storage.get_users(pool)
        if match.group(1):
            return await chat.send_text(len(users))
        text = '. {first_name}, {id} [n{sub_news}v{sub_video}m{sub_msg}]'
        text = '\n'.join([str(i+1)+text.format(**user)
                          for i, user in enumerate(users)])
        await chat.send_text(text)


@bot.command(r'/dbstat')
async def dbstat(chat, match):
    if chat.sender['id'] in settings.ADMINS:
        logger.debug('dbstat')
        data = await storage.get_stats(pool)
        users = await storage.get_users(pool)
        dbupdates = '\n'.join(['{}: {}'.format(k, str(v))
                               for k, v in sorted(data.items()) if v])
        userscount = 'Пользователи: {}\n'.format(len(users))
        await chat.send_text(userscount + dbupdates)


# Basic commands


@bot.command(r'/?(menu|меню)')
async def menu(chat, match):
    text = 'Выбери пункт меню 👇'
    kb = keyboard()
    await storage.set_user(pool, **chat.sender)
    await send_keyboard(chat, match.group(1), text, kb)


@bot.command(r'(/start)')
async def start(chat, match):
    kb = keyboard()
    await storage.set_user(pool, **chat.sender)
    await send_keyboard(chat, match.group(1), settings.START_TEXT, kb)


@bot.command(r'(/stop)')
@bot.command(r'(/delete)')
async def stop(chat, match):
    logger.info('%s: Стоп', chat.sender['id'])
    await storage.delete_user(pool, **chat.sender)
    await chat.reply(settings.STOP_TEXT)


@bot.default
@bot.command(r'/?(help|помощь|справка)')
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
    pool = await aioredis.create_pool(
        (host, 6379),
        encoding='utf-8',
        minsize=5,
        maxsize=10)
    await bot.loop()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    try:
        logger.info('bot started')
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        bot.stop()
