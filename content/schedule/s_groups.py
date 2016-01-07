import logging
import ujson
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from time import time
from multiprocessing.pool import ThreadPool

start = time()

logger = logging.getLogger("ScheduleToJSON")

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

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.INFO)
    result = {k: v for i in schedule() for k, v in i.items()}
    with open('s_groups.json', 'w') as outfile:
        ujson.dump(result, outfile)
    print('It took', round(time()-start, 2), 'seconds.')