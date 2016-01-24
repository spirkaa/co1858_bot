import logging
import time
import asyncio
import schedule as cron
from content.scrapers import media, schedule

logger = logging.getLogger('db_update')

loop = asyncio.get_event_loop()


def update_media():
    loop.run_until_complete(media.main(loop))
    logger.debug('update_media end')


def update_schedule():
    loop.run_until_complete(schedule.main(loop))
    logger.debug('update_schedule end')


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)

    logger.info('cron scheduler started')
    try:
        cron.every(10).minutes.do(update_media)
    except:
        pass
    try:
        cron.every().hour.do(update_schedule)
    except:
        pass

    while True:
        cron.run_pending()
        time.sleep(1)
