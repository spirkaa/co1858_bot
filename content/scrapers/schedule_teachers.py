import logging
import os
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

logger = logging.getLogger(__name__)
logging.getLogger('selenium').setLevel(logging.WARNING)

url = 'https://mrko.mos.ru/dnevnik/'
login = 'login'
password = 'password'


def drv():
    host = os.environ.get('SELENIUM_HOST', 'localhost')
    cmd_exec = 'http://{}:4444/wd/hub'.format(host)
    caps = DesiredCapabilities.FIREFOX
    driver = webdriver.Remote(command_executor=cmd_exec,
                              desired_capabilities=caps)
    return driver


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


def collect():
    driver = drv()
    driver.get(url)
    driver.find_element_by_id('login').send_keys(login)
    driver.find_element_by_id('pass').send_keys(password)
    driver.find_element_by_xpath('//*[@id="em_enter"]/input[4]').click()
    sleep(1)
    driver.get(url + 'services/rasp.php?m=4&day=1')
    sleep(1)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    schedule_table = soup.select_one('table[id=busynessTable] tbody')
    links = schedule_table.select('tr a[href^=javascript]')
    links = [link.attrs.get('href').split("'")[1] for link in links]
    schedule = {}
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
    logger.debug('schedule_teachers end')
    return schedule


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(name)s:%(lineno)s] %(levelname)s - %(message)s',
        level=logging.DEBUG)

    result = collect()
    print(len(result))

    import ujson
    with open('s_teachers.json', 'w') as outfile:
        ujson.dump(result, outfile)
