import logging
from datetime import datetime
import asyncio
import psycopg2
import sqlalchemy as sa
from sqlalchemy.schema import CreateTable
from aiopg.sa import create_engine


logger = logging.getLogger(__name__)

metadata = sa.MetaData()
users = sa.Table('users', metadata,
                 sa.Column('db_id', sa.Integer, primary_key=True),
                 sa.Column('created', sa.DateTime),
                 sa.Column('id', sa.BigInteger, unique=True),
                 sa.Column('username', sa.String(255)),
                 sa.Column('first_name', sa.String(255)),
                 sa.Column('last_name', sa.String(255)),
                 sa.Column('sub_msg', sa.Boolean),
                 sa.Column('sub_news', sa.Boolean),
                 sa.Column('sub_video', sa.Boolean))


@asyncio.coroutine
def eng():
    engine = yield from create_engine(user='login',
                                      database='co1858_bot',
                                      host='127.0.0.1')
    return engine


@asyncio.coroutine
def db_create():
    engine = yield from eng()
    with (yield from engine) as conn:
        try:
            yield from conn.execute(CreateTable(users))
            logger.debug('Table created')
        except psycopg2.ProgrammingError as e:
            logger.error(e.pgerror)


@asyncio.coroutine
def db_check_or_create(**kwargs):
    engine = yield from eng()
    with (yield from engine) as conn:
        query = (sa.select([users]).where(users.c.id == kwargs['id']))
        res = yield from conn.execute(query)
        if res.rowcount == 0:
            try:
                q = (users.insert().values(created=datetime.now(),
                                           sub_msg=True,
                                           sub_news=True,
                                           sub_video=True,
                                           **kwargs))
                yield from conn.execute(q)
                logger.debug('id %s added', kwargs['id'])
            except psycopg2.IntegrityError as e:
                logger.debug(e.pgerror)
        else:
            logger.debug('id %s already exists', kwargs['id'])


@asyncio.coroutine
def db_select(target=None, **kwargs):
    engine = yield from eng()
    with (yield from engine) as conn:
        if target == 'msg':
            query = (sa.select([users.c.id])
                     .where(users.c.sub_msg == True))  # noqa
        elif target == 'news':
            query = (sa.select([users.c.id])
                     .where(users.c.sub_news == True))  # noqa
        elif target == 'video':
            query = (sa.select([users.c.id])
                     .where(users.c.sub_video == True))  # noqa
        else:
            query = (sa.select([users]))
        res = yield from conn.execute(query)
        return res


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(db_create())

    from random import randint

    def random_n_digits(n):
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)
    random_id = random_n_digits(9)

    loop.run_until_complete(db_check_or_create(id=random_id, username='Testr'))
    loop.run_until_complete(db_check_or_create(id=133914054))
