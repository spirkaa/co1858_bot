import ujson
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

brew = '/opt/homebrew-cask/Caskroom'
ff = '/firefox/41.0.1/Firefox.app/Contents/MacOS/firefox-bin'
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
    shedule_table = soup.select_one('table[id=busynessTable] tbody')
    links = shedule_table.select('tr a[href^=javascript]')
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


def main():
    shedule = {}
    links = collect_links()
    for link in links:
        driver.get(url + 'services/' + link)
        sleep(0.5)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        name = soup.select_one('p').get_text().replace('Учитель: ', '')
        rows = soup.select('tbody tr')[1:]
        table = [[col.text for col in row.select('td')] for row in rows]
        shedule[name] = table_to_dict(table)
    driver.quit()

    with open('s_teachers.json', 'w') as outfile:
        ujson.dump(shedule, outfile)


if __name__ == '__main__':
    main()