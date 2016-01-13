import logging
import asyncio
import os
import aioredis
from concurrent.futures import ProcessPoolExecutor
from storage import set_schedule
import content.scrapers.schedule_groups as groups
import content.scrapers.schedule_teachers as teachers


logger = logging.getLogger('scraper_schedule')


async def add_to_storage(schedule_type, schedule):
    host = os.environ.get('REDIS_HOST', 'localhost')
    pool = await aioredis.create_pool(
        (host, 6379),
        encoding="utf-8",
        minsize=5,
        maxsize=10)
    await set_schedule(pool, schedule_type, schedule)
    await pool.clear()


async def main(loop):
    executor = ProcessPoolExecutor(2)
    t = loop.run_in_executor(executor, teachers.collect)
    g = loop.run_in_executor(executor, groups.collect)
    tres = await t
    gres = await g
    await add_to_storage('teachers', tres)
    await add_to_storage('groups', gres)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
