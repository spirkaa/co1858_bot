import logging
import os
import textwrap
import asyncio
import aiohttp
import aioredis
from bs4 import BeautifulSoup
from storage import set_media

logger = logging.getLogger(__name__)


async def get_source(url):
    response = await aiohttp.get(url)
    return await response.text()


async def parse_news():
    url = 'http://sch1858uv.mskobr.ru'
    r = await get_source(url + '/novosti/')
    soup = BeautifulSoup(r, 'lxml')
    newsblock = soup.select('.kris-news-box')
    articles = {}
    titles = {}
    for index, v in enumerate(newsblock):
        article = newsblock[index]
        date = article.select_one('.kris-news-data-txt').text
        title = article.select_one('.h3').text
        try:
            img = url + article.select_one('img').attrs.get('src')
        except AttributeError:
            img = ''
        body = article.select_one('.kris-news-body').text
        try:
            more = url + article.select_one('.link_more').attrs.get('href')
        except AttributeError:
            more = ''
        article = dict(title=title, date=date, body=body, more=more, img=img)
        articles[index] = article
        titles[index] = '{}. {}'.format(
            index,
            textwrap.shorten(title, width=25, placeholder='…'))
    return [articles, titles]


async def parse_video():
    url = 'http://www.youtube.com'
    r = await get_source(url + '/user/co1858/videos')
    soup = BeautifulSoup(r, 'lxml')
    videoblock = soup.select('.yt-lockup-title')
    articles = {}
    titles = {}
    for index, v in enumerate(videoblock):
        video = videoblock[index]
        link = url + video.select_one('a').attrs.get('href')
        title = video.select_one('a').attrs.get('title')
        article = dict(link=link)
        articles[index] = article
        titles[index] = '{}. {}'.format(
            index,
            textwrap.shorten(title, width=25, placeholder='…'))
    return [articles, titles]


async def main(loop):
    host = os.environ.get('REDIS_HOST', 'localhost')
    pool = await aioredis.create_pool((host, 6379), encoding="utf-8", minsize=5, maxsize=10)
    n = asyncio.ensure_future(parse_news(), loop=loop)
    v = asyncio.ensure_future(parse_video(), loop=loop)
    news = await n
    video = await v
    await set_media(pool, 'news', news[0], news[1])
    await set_media(pool, 'video', video[0], video[1])
    await pool.clear()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
