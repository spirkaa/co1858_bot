import logging
import ujson
from settings import SUBS

logger = logging.getLogger(__name__)


async def dict_to_keys(**sender):
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
    async with pool.get() as redis:
        await redis.select(0)
        pairs = await dict_to_keys(**sender)
        tr = redis.multi_exec()
        tr.hmset(*pairs)
        for name, sub in SUBS.items():
            tr.hsetnx(pairs[0], sub, '1')
        await tr.execute()
        val = await redis.hgetall(pairs[0])
        logger.debug('%s %s', pairs[0], val)


async def get_user(pool, chat_id):
    async with pool.get() as redis:
        await redis.select(0)
        user = await redis.hgetall(chat_id)
        return user


async def get_users(pool, target=None):
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
    async with pool.get() as redis:
        await redis.select(0)
        redis.hset(chat_id, key, val)


async def delete_user(pool, **sender):
    async with pool.get() as redis:
        await redis.select(0)
        key = await dict_to_keys(**sender)
        await redis.delete(key[0])
        logger.debug('%s deleted from storage', key[0])


async def set_schedule(pool, schedule_type, schedule):
    async with pool.get() as redis:
        await redis.select(2)
        await redis.set('schedule:{}'.format(schedule_type), ujson.dumps(schedule))
        await redis.select(0)


async def get_schedule(pool, schedule_type):
    async with pool.get() as redis:
        await redis.select(2)
        schedule = await redis.get('schedule:{}'.format(schedule_type))
        await redis.select(0)
        return schedule


async def set_media(pool, content_type, articles, titles):
    async with pool.get() as redis:
        await redis.select(1)
        tr = redis.multi_exec()
        for k, v in articles.items():
            tr.set('{}:{}'.format(content_type, k), ujson.dumps(v))
        titles_key = '{}:titles'.format(content_type)
        tr.delete(titles_key)
        tr.rpush(titles_key, *list(titles.values()))
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
