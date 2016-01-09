import logging
import ujson
from keyboard import keyboard, scraper_btns
from storage import get_article, get_titles

logger = logging.getLogger(__name__)


async def send_news(chat, redis, index=0):
    logger.debug('send_news start')
    # await chat.send_chat_action(action='typing')
    article = await get_article(redis, 'news', index)
    article = ujson.loads(article)
    titles = await get_titles(redis, 'news')
    text = '[📰]({img}) *{title} ({date})*{body}\n🔎 [Подробнее…]({more})'.format(**article)
    buttons = scraper_btns(titles, '📰')
    kb = keyboard(buttons)
    logger.info('%s: send_news', chat.sender['id'])
    await chat.send_text(
        text,
        parse_mode='Markdown',
        reply_markup=ujson.dumps(kb))
    logger.info('%s: send_news', chat.sender['id'])


async def send_video(chat, redis, index=0):
    logger.debug('send_video start')
    await chat.send_chat_action(action='typing')
    article = await get_article(redis, 'video', index)
    article = ujson.loads(article)
    titles = await get_titles(redis, 'video')
    buttons = scraper_btns(titles, '🎥')
    kb = keyboard(buttons)
    logger.info('%s: send_video', chat.sender['id'])
    await chat.send_text(article['link'], reply_markup=ujson.dumps(kb))
    logger.info('%s: send_video', chat.sender['id'])
