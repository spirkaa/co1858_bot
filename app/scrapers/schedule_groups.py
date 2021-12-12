import logging
import os
import ujson
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from multiprocessing.pool import ThreadPool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('oauth2client').setLevel(logging.WARNING)


json_key = os.path.join(BASE_DIR, 'gspreadtoken.json')
scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)

table = '1BwJnx15AjrUWemGxIthW4L14xI3_GSEykOXSac-jHBk'
day_coords = {
    'mon': {'num': 0,
            'name': 1,
            'aud': 2,
            'row_start': 2,
            'row_end': 10},
    'tue': {'num': 0,
            'name': 1,
            'aud': 2,
            'row_start': 12,
            'row_end': 20},
    'wed': {'num': 0,
            'name': 1,
            'aud': 2,
            'row_start': 22,
            'row_end': 30},
    'thu': {'num': 4,
            'name': 5,
            'aud': 6,
            'row_start': 2,
            'row_end': 10},
    'fri': {'num': 4,
            'name': 5,
            'aud': 6,
            'row_start': 12,
            'row_end': 20}
    }


def get_sheet(index):
    gc = gspread.authorize(credentials)
    return gc.open_by_key(table).get_worksheet(index).get_all_values()


def get_schedule(sheet):
    lessons = {}
    group = '0'
    for k, v in day_coords.items():
        group = sheet[0][0]
        day = {}
        for x in range(v['row_start'], v['row_end'] + 1):
            row = sheet[x]
            day[row[v['num']]] = [row[v['name']], row[v['aud']]]
        lessons[k] = day
    return {group: lessons}


def sheets():
    with ThreadPool(12) as pool:
        return pool.map(get_sheet, range(48, 77))


def schedule():
    groups = sheets()
    with ThreadPool(12) as pool:
        return pool.map(get_schedule, groups)


def collect():
    res = {k: v for i in schedule() for k, v in i.items()}
    return res


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)

    result = collect()
    print(len(result))

    with open('s_groups.json', 'w') as outfile:
        ujson.dump(result, outfile)
