import logging
import ujson

logger = logging.getLogger(__name__)


async def dict_to_keys(**sender):
    keys = []
    for k, v in sender.items():
        # logger.debug(k)
        if k == 'id':
            keys.insert(0, v)
        else:
            keys.append(k)
            keys.append(v)
    return keys


async def iscan(redis):
    keys = []
    async for key in redis.iscan():
        keys.append(key)
        # logger.debug(key)
    return keys


async def flushdb(redis, dbindex):
    await redis.select(dbindex)
    await redis.flushdb()


async def set_user(redis, **sender):
    await redis.select(0)
    keys = await dict_to_keys(**sender)
    tr = redis.multi_exec()
    tr.hmset(*keys)
    subs = ['sub_msg', 'sub_news', 'sub_video']
    for sub in subs:
        tr.hsetnx(keys[0], sub, '1')
    await tr.execute()
    val = await redis.hgetall(keys[0])
    logger.debug('%s %s', keys[0], val)


async def get_users(redis, target=None):
    keys = await iscan(redis)
    subbed = []
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


async def delete_user(redis, **sender):
    keys = await dict_to_keys(**sender)
    logger.debug('%s deleted from storage', keys[0])
    await redis.delete(keys[0])


async def set_schedule(redis, schedule_type, schedule):
    await redis.select(2)
    await redis.set('schedule:{}'.format(schedule_type), ujson.dumps(schedule))
    await redis.select(0)


async def get_schedule(redis, schedule_type):
    await redis.select(2)
    schedule = await redis.get('schedule:{}'.format(schedule_type))
    await redis.select(0)
    return schedule


async def set_media(redis, content_type, articles, titles, *args, **kwargs):
    logger.debug('add_from_scraper start')
    await redis.select(1)
    tr = redis.multi_exec()
    for k, v in articles.items():
        tr.set('{}:{}'.format(content_type, k), ujson.dumps(v))
    titles_key = '{}:titles'.format(content_type)
    tr.delete(titles_key)
    tr.rpush(titles_key, *list(titles.values()))
    await tr.execute()
    val2 = await redis.lrange('{}:titles'.format(content_type), 0, -1)
    print(type(val2), len(val2), val2)
    await redis.select(0)
    logger.debug('add_from_scraper end')


async def get_media(redis, content_type, index=0):
    # logger.debug('get_article start')
    await redis.select(1)
    article = await redis.get('{}:{}'.format(content_type, index))
    await redis.select(0)
    # logger.debug('get_article stop')
    return article


async def get_media_titles(redis, content):
    # logger.debug('get_titles start')
    await redis.select(1)
    titles = await redis.lrange('{}:titles'.format(content), 0, -1)
    await redis.select(0)
    # logger.debug('get_titles stop')
    return titles
