import logging
import asyncio
import os
from time import sleep, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from storage import set_schedule
import aioredis
from concurrent.futures import ProcessPoolExecutor

start = time()

logger = logging.getLogger(__name__)
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

brew = '/opt/homebrew-cask/Caskroom'
ff = '/firefox/43.0.4/Firefox.app/Contents/MacOS/firefox-bin'
path = '{}{}'.format(brew, ff)
driver = webdriver.Firefox(firefox_binary=FirefoxBinary(path))

url = 'https://mrko.mos.ru/dnevnik/'


def collect_links():
    driver.get(url)
    driver.find_element_by_id('login').send_keys('login')
    driver.find_element_by_id('pass').send_keys('password')
    driver.find_element_by_xpath('//*[@id="em_enter"]/input[4]').click()
    sleep(1)
    driver.get(url + 'services/rasp.php?m=4&day=1')
    sleep(1)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    schedule_table = soup.select_one('table[id=busynessTable] tbody')
    links = schedule_table.select('tr a[href^=javascript]')
    return [link.attrs.get('href').split("'")[1] for link in links]


def table_to_dict(table):
    rasp = {}
    daynames = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    wknd = ['sat', 'sun']
    ''' zip(*table) меняет местами ряды и колонки #
        [[1, 2, 3],   ->   [(1, 4, 7),
         [4, 5, 6],   ->    (2, 5, 8),
         [7, 8, 9]]   ->    (3, 6, 9)]
    '''
    for index, day in enumerate(zip(*table)):
        daydict = {}
        for i, lesson in enumerate(day):
            daydict[i+1] = lesson
        dayname = daynames[index]
        rasp[dayname] = daydict
    for k in wknd:
        rasp.pop(k, None)
    return rasp


def s_teachers():
    schedule = {}
    links = collect_links()
    for link in links:
        logger.debug(link)
        driver.get(url + 'services/' + link)
        sleep(0.5)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        name = soup.select_one('p').get_text().replace('Учитель: ', '')
        rows = soup.select('tbody tr')[1:]
        table = [[col.text for col in row.select('td')] for row in rows]
        schedule[name] = table_to_dict(table)
    driver.quit()
    return schedule


import ujson
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from time import time
from multiprocessing.pool import ThreadPool

json_key = ujson.load(open('gspreadtoken.json'))
scope = ['https://spreadsheets.google.com/feeds']
credentials = SignedJwtAssertionCredentials(
    json_key['client_email'],
    json_key['private_key'].encode(),
    scope)


table = 'Расписание уроков на 2015-2016 учебный год (экраны)'
days = {
    'mon': {'num': 'A',
            'name': 'B',
            'aud': 'C',
            'row_start': 3,
            'row_end': 11},
    'tue': {'num': 'A',
            'name': 'B',
            'aud': 'C',
            'row_start': 13,
            'row_end': 21},
    'wed': {'num': 'A',
            'name': 'B',
            'aud': 'C',
            'row_start': 23,
            'row_end': 31},
    'thu': {'num': 'E',
            'name': 'F',
            'aud': 'G',
            'row_start': 3,
            'row_end': 11},
    'fri': {'num': 'E',
            'name': 'F',
            'aud': 'G',
            'row_start': 13,
            'row_end': 21}
    }


def get_sheet(index):
    logger.info('Collect sheet %s', index)
    gc = gspread.authorize(credentials)
    return gc.open(table).get_worksheet(index)


def get_schedule(wks):
    uroki = {}
    for k, v in days.items():
        klass = wks.acell('A1').value
        logger.info('%s, %s', klass, k)
        day = {}
        for x in range(v['row_start'], v['row_end'] + 1):
            num = v['num'] + str(x)  # A13
            name = v['name'] + str(x)  # B13
            aud = v['aud'] + str(x)  # C13
            # day[A13] = [B13, C13]
            day[wks.acell(num).value] = [wks.acell(name).value,
                                         wks.acell(aud).value]
        uroki[k] = day
    return {klass: uroki}


def sheets():
    logger.info('Collect sheets...')
    with ThreadPool(12) as pool:
        return pool.map(get_sheet, range(48, 75))


def schedule():
    groups = sheets()
    logger.info('Collect schedule...')
    with ThreadPool(12) as pool:
        return pool.map(get_schedule, groups)


def s_groups():
    return {k: v for i in schedule() for k, v in i.items()}


async def add_to_storage(schedule_type, schedule):
    host = os.environ.get('REDIS_HOST', 'localhost')
    redis = await aioredis.create_redis((host, 6379), encoding="utf-8")
    await set_schedule(redis, schedule_type, schedule)
    redis.close()


async def main(loop):
    executor = ProcessPoolExecutor(2)
    t = loop.run_in_executor(executor, s_teachers)
    g = loop.run_in_executor(executor, s_groups)
    tr = await t
    gr = await g
    await add_to_storage('teachers', tr)
    await add_to_storage('groups', gr)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)
    logger.debug('__file__ start')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    logger.debug('__file__ end')
    print('It took', round(time()-start, 2), 'seconds.')
