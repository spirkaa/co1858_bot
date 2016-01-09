import logging
import textwrap
import aiohttp
from bs4 import BeautifulSoup
from storage import set_media

logger = logging.getLogger(__name__)


async def get_source(url):
    response = await aiohttp.get(url)
    return await response.text()


async def parse_news():
    logger.debug('parse_news start')
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
        except:
            img = ''
        body = article.select_one('.kris-news-body').text
        more = url + article.select_one('.link_more').attrs.get('href')
        article = dict(title=title, date=date, body=body, more=more, img=img)
        articles[index] = article
        titles[index] = '{}. {}'.format(
            index,
            textwrap.shorten(title, width=25, placeholder='…'))
    logger.debug('parse_news end')
    return [articles, titles]


async def parse_video():
    logger.debug('parse_video start')
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
    logger.debug('parse_video end')
    return [articles, titles]


async def main():
    logger.debug('main() start')
    import os
    import aioredis
    host = os.environ.get('REDIS_HOST', 'localhost')
    redis = await aioredis.create_redis((host, 6379), encoding="utf-8")
    news = await parse_news()
    video = await parse_video()
    await set_media(redis, 'news', news[0], news[1])
    await set_media(redis, 'video', video[0], video[1])
    logger.debug('main() end')


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)
    logger.debug('__file__ start')
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    logger.debug('__file__ end')
