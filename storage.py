import logging
import datetime
import time
import ujson
from settings import SUBS

logger = logging.getLogger(__name__)


def unix_time(time_):
    return int(time.mktime(time_.timetuple()))


def norm_time(ts):
    return datetime.datetime.fromtimestamp(ts)


def dict_to_keys(**sender):
    keys = []
    for k, v in sender.items():
        if k == 'id':
            keys.insert(0, v)
        else:
            keys.append(k)
            keys.append(v)
    return keys


async def flushdb(pool, dbindex):
    async with pool.get() as redis:
        await redis.select(dbindex)
        await redis.flushdb()


async def set_user(pool, **sender):
    now = unix_time(datetime.datetime.now())
    async with pool.get() as redis:
        await redis.select(0)
        pairs = dict_to_keys(**sender)
        tr = redis.multi_exec()
        tr.hmset(*pairs)
        for name, sub in SUBS.items():
            tr.hsetnx(pairs[0], sub, '1')
        tr.hsetnx(pairs[0], 'created', now)
        tr.hsetnx(pairs[0], 'modified', now)
        await tr.execute()
        logger.debug('%s %s', pairs[0], await redis.hgetall(pairs[0]))


async def get_user(pool, chat_id):
    async with pool.get() as redis:
        await redis.select(0)
        user = await redis.hgetall(chat_id)
        logger.debug('get_user %s', user)
        return user


async def get_users(pool):
    async with pool.get() as redis:
        await redis.select(0)
        keys = await redis.keys('*')
        users = []
        for key in keys:
            data = await redis.hgetall(key)
            data['id'] = key
            users.append(data)
        return users


async def get_users_sub(pool, target):
    async with pool.get() as redis:
        subbed = []
        await redis.select(0)
        keys = await redis.keys('*')
        for key in keys:
            sub = '0'
            if target == 'msg':
                sub = await redis.hget(key, 'sub_msg')
            elif target == 'news':
                sub = await redis.hget(key, 'sub_news')
            elif target == 'video':
                sub = await redis.hget(key, 'sub_video')
            if sub == '1':
                subbed.append(key)
        return subbed


async def update_user(pool, chat_id, key, val):
    now = unix_time(datetime.datetime.now())
    async with pool.get() as redis:
        await redis.select(0)
        await redis.hset(chat_id, key, val)
        await redis.hset(chat_id, 'modified', now)


async def delete_user(pool, key=None, **sender):
    async with pool.get() as redis:
        await redis.select(0)
        if key:
            await redis.delete(key)
            logger.info('%s deleted: he kick us!', key)
        else:
            key = dict_to_keys(**sender)
            await redis.delete(key[0])
            logger.info('%s deleted: /stop', key[0])


async def set_schedule(pool, schedule_type, schedule):
    now = unix_time(datetime.datetime.now())
    async with pool.get() as redis:
        await redis.select(2)
        await redis.set('schedule:{}'.format(schedule_type), ujson.dumps(schedule))
        await redis.set('schedule:{}:modified'.format(schedule_type), now)
        await redis.select(0)


async def get_schedule(pool, schedule_type):
    async with pool.get() as redis:
        await redis.select(2)
        schedule = await redis.get('schedule:{}'.format(schedule_type))
        await redis.select(0)
        return schedule


async def set_media(pool, content_type, articles, titles):
    now = unix_time(datetime.datetime.now())
    async with pool.get() as redis:
        await redis.select(1)
        tr = redis.multi_exec()
        for k, v in articles.items():
            tr.set('{}:{}'.format(content_type, k), ujson.dumps(v))
        titles_key = '{}:titles'.format(content_type)
        tr.delete(titles_key)
        tr.rpush(titles_key, *list(titles.values()))
        tr.set('{}:modified'.format(content_type), now)
        await tr.execute()
        await redis.select(0)


async def get_media(pool, content_type, index=0):
    async with pool.get() as redis:
        await redis.select(1)
        article = await redis.get('{}:{}'.format(content_type, index))
        await redis.select(0)
        return article


async def get_media_titles(pool, content):
    async with pool.get() as redis:
        await redis.select(1)
        titles = await redis.lrange('{}:titles'.format(content), 0, -1)
        await redis.select(0)
        return titles


async def get_stats(pool):
    async with pool.get() as redis:
        slug = 'modified'
        dates = {}
        await redis.select(1)
        dates['m_news'] = await redis.get('news:{}'.format(slug))
        dates['m_video'] = await redis.get('video:{}'.format(slug))
        await redis.select(2)
        s = 'schedule'
        dates['s_teachers'] = await redis.get('{}:teachers:{}'.format(s, slug))
        dates['s_groups'] = await redis.get('{}:groups:{}'.format(s, slug))
        await redis.select(0)
        for k, v in dates.items():
            if v:
                dates[k] = norm_time(float(v))
        return dates
