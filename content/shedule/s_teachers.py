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
shedule_table = soup.select_one('table[id=busynessTable] tbody')
links = shedule_table.select('tr a[href^=javascript]')
teacher_links = [link.attrs.get('href').split("'")[1] for link in links]


def table_to_dict(lessons, daynum):
    days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    result = {days[daynum]: {i+1: lesson[daynum]
                             for i, lesson
                             in enumerate(lessons)}}
    return result


shedule = {}
for link in teacher_links:
    driver.get(url + 'services/' + link)
    sleep(0.5)
    soup = BeautifulSoup(driver.page_source)
    name = soup.select_one('p').get_text().replace('Учитель: ', '')
    rows = soup.select('tbody tr')[1:]
    lessons = [[col.text for col in row.select('td')] for row in rows]
    rasp = [table_to_dict(lessons, x) for x in range(1, 7)]
    raspdict = {k: v for day in rasp for k, v in day.items()}
    shedule[name] = raspdict


with open('s_teachers.json', 'w') as outfile:
    json.dump(shedule, outfile)

driver.quit()
