import logging
import ujson
import aiohttp
from bs4 import BeautifulSoup
from keyboard import keyboard, scraper_btns

logger = logging.getLogger(__name__)


async def get_source(url):
    response = await aiohttp.get(url)
    return await response.text()


async def send_news(chat, index=0):
    await chat.send_chat_action(action='typing')
    url = 'http://sch1858uv.mskobr.ru'
    r = await get_source(url + '/novosti/')
    soup = BeautifulSoup(r, 'lxml')
    newsblock = soup.select('.kris-news-box')
    logger.debug(newsblock)
    article = newsblock[index]
    date = article.select_one('.kris-news-data-txt').text
    title = article.select_one('.h3').text
    try:
        img = url + article.select_one('img').attrs.get('src')
    except:
        img = ''
    body = article.select_one('.kris-news-body').text
    more = url + article.select_one('.link_more').attrs.get('href')
    news = [title, date, body, more, img]
    text = '[📰]({4}) *{0} ({1})*{2}\n🔎 [Подробнее…]({3})'.format(*news)
    buttons = scraper_btns(newsblock, 'news', '📰')
    kb = keyboard(buttons)
    logger.info('%s: send_news', chat.sender['id'])
    await chat.send_text(
        text,
        parse_mode='Markdown',
        reply_markup=ujson.dumps(kb))


async def send_video(chat, index=0):
    await chat.send_chat_action(action='typing')
    url = 'http://www.youtube.com'
    r = await get_source(url + '/user/co1858/videos')
    soup = BeautifulSoup(r, 'lxml')
    videoblock = soup.select('.yt-lockup-title')
    logger.debug(videoblock)
    video = videoblock[index]
    link = video.select_one('a').attrs.get('href')
    buttons = scraper_btns(videoblock, 'video', '🎥')
    kb = keyboard(buttons)
    logger.info('%s: send_video', chat.sender['id'])
    await chat.send_text(url + link, reply_markup=ujson.dumps(kb))
