import re
import json
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

binary = FirefoxBinary('/opt/homebrew-cask/Caskroom/firefox/41.0.1/Firefox.app/Contents/MacOS/firefox-bin')
driver = webdriver.Firefox(firefox_binary=binary)

url = 'https://mrko.mos.ru/dnevnik/'
driver.get(url)

driver.find_element_by_id('login').send_keys('login')
driver.find_element_by_id('pass').send_keys('password')
driver.find_element_by_xpath('//*[@id="em_enter"]/input[4]').click()
sleep(1)
driver.get(url + 'services/rasp.php?m=4&day=1')
sleep(1)
soup = BeautifulSoup(driver.page_source)
rasp = soup.select('table[id=busynessTable] tbody')[0]
teachers = rasp.select('tr a[href^=javascript]')
teacher_pages = []
for teacher in teachers:
    r = re.compile(r'\'.+\',')
    c = r.search(teacher.attrs.get('href')).group(0)
    c = re.sub(r'[\',]', '', c)
    teacher_pages.append(c)


def table_to_dict(spisok, daynum):
    week = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    slov = {}
    for i, urok in enumerate(spisok):
        slov[i+1] = urok[daynum]
    return {week[daynum]: slov}

raspisanie = {}
for page in teacher_pages:
    driver.get(url + 'services/' + page)
    sleep(1)
    soup = BeautifulSoup(driver.page_source)
    name = soup.select('p')[0].get_text().replace('Учитель: ', '')
    rows = soup.select('tbody tr')[1:]
    uroki = []
    for row in rows:
        cols = row.select('td')
        cols = [col.text for col in cols]
        uroki.append([col for col in cols])
    rasp = []
    for x in range(1, 7):
        rasp.append(table_to_dict(uroki, x))
    raspdict = {}
    for day in rasp:
        for k, v in day.items():
            raspdict[k] = v
    raspisanie[name] = raspdict


with open('s_teachers.json', 'w') as outfile:
    json.dump(raspisanie, outfile)

driver.quit()
