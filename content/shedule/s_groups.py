import logging
import json
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from time import time
from multiprocessing.pool import ThreadPool

start = time()

logger = logging.basicConfig(
    format='%(asctime)s  [%(name)s:%(lineno)s]  %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger("SheduleToJSON")

json_key = json.load(open('gspreadtoken.json'))
scope = ['https://spreadsheets.google.com/feeds']
credentials = SignedJwtAssertionCredentials(
    json_key['client_email'],
    json_key['private_key'].encode(),
    scope)


table = 'Расписание уроков на 2015-2016 учебный год (экраны)'
days = {
    'mon': ['A', 'B', 'C', 3, 11],
    'tue': ['A', 'B', 'C', 13, 21],
    'wed': ['A', 'B', 'C', 23, 31],
    'thu': ['E', 'F', 'G', 3, 11],
    'fri': ['E', 'F', 'G', 13, 21]
    }


def get_sheet(index):
    logger.info('Collect sheet %s', index)
    gc = gspread.authorize(credentials)
    return gc.open(table).get_worksheet(index)


def get_shedule(wks):
    uroki = {}
    for k, v in days.items():
        klass = wks.acell('A1').value
        logger.info('%s, %s', klass, k)
        day = {}
        for x in range(v[3], v[4] + 1):
            num = v[0] + str(x)
            name = v[1] + str(x)
            aud = v[2] + str(x)
            day[wks.acell(num).value] = [wks.acell(name).value,
                                         wks.acell(aud).value]
        uroki[k] = day
    return {klass: uroki}


def sheets():
    logger.info('Collect sheets...')
    with ThreadPool(12) as pool:
        return pool.map(get_sheet, range(48, 75))


def shedule():
    groups = sheets()
    logger.info('Collect shedule...')
    with ThreadPool(12) as pool:
        return pool.map(get_shedule, groups)

if __name__ == '__main__':
    result = {}
    for i in shedule():
        for k, v in i.items():
            result[k] = v
    with open('s_groups.json', 'w') as outfile:
        json.dump(result, outfile)
    print('It took', round(time()-start, 2), 'seconds.')
