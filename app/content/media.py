import logging
import ujson

from storage import get_media, get_media_titles
from keyboard import keyboard, scraper_btns

logger = logging.getLogger(__name__)


async def send_news(chat, redis, index=0):
    article = await get_media(redis, 'news', index)
    article = ujson.loads(article)
    titles = await get_media_titles(redis, 'news')
    text = '[📰]({img}) *{title} ({date})*{body}\n🔎 [Подробнее…]({more})'.format(**article)
    buttons = scraper_btns(titles, '📰')
    kb = keyboard(buttons)
    await chat.send_text(
        text,
        parse_mode='Markdown',
        reply_markup=ujson.dumps(kb))
    logger.info('%s: send_news', chat.sender['id'])


async def send_video(chat, redis, index=0):
    article = await get_media(redis, 'video', index)
    article = ujson.loads(article)
    titles = await get_media_titles(redis, 'video')
    buttons = scraper_btns(titles, '🎥')
    kb = keyboard(buttons)
    await chat.send_text(article['link'], reply_markup=ujson.dumps(kb))
    logger.info('%s: send_video', chat.sender['id'])
