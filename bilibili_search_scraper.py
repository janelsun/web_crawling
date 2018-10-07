'''
Bilibili Search Result Page Video Info Scraper

This is a web scraper written using mostly selenium (for navigatin between pages) and Beautifulsoup (for parsing HTML elements)
Final result would be written to a csv file
data = {
'title': str,
'desctiption': str,
'view count': int,
'danmu count': int,
'owner': str,
'date': str, # refers to the date of upload
}

script written by: Janel Sun
All rights reserved
'''

from bs4 import BeautifulSoup
import pandas as pd
import time
import sys

from selenium import webdriver
# from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0 
from selenium.webdriver.common.action_chains import ActionChains

if len(sys.argv) > 1:
    keyword = str(sys.argv[1])
else:
    keyword = '罗云熙' # default searching param


class Bilibili:
    def __init__(self, keyword):
        self.driver = webdriver.Chrome()  # path of your chrome driver
        # self.wait = WebDriverWait(self.driver, 10)
        self.url = 'https://www.bilibili.com'  # url of main page
        self.keyword = keyword  

    def get_driver(self):
        return self.driver

    def create_dic(self):
        dic = {
            'title': [],
            'description': [],
            'view count': [],
            'danmu count': [],
            'owner': [],
            'date': [],
        }
        return dic

    def init_df(self):
        dic = self.create_dic()
        df = pd.DataFrame(dic)
        return df

    def open_page(self):
        url = self.url
        self.driver.get(url)

    # searching
    def search(self):
        self.open_page()
        main_page = self.driver.current_window_handle
        search_link = self.driver.find_element_by_css_selector('input[type="text"]')
        ActionChains(self.driver).move_to_element(search_link).click().perform()
        time.sleep(1) # time.sleep() has been used to allow the page to load properly, could use WebDriverWait to wait for element appearance instead 
        search_link.send_keys(self.keyword)
        search_button = self.driver.find_element_by_css_selector('button[type="submit"]')
        search_button.click()
        windows = self.driver.window_handles
        curr = self.driver.switch_to_window(windows[1])
        time.sleep(2)

    # retrieve data from result page
    def get_data(self):
        driver = self.driver
        time.sleep(5) 
        dic = self.create_dic()

        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        if soup.head.title.text.find(self.keyword) > -1:
            print('成功跳转')
        else:
            print('跳转失败')
        time.sleep(2)
        items = soup.find_all('li', {'class': 'video matrix'})
        for item in items:
            title = item.find('a').get('title')
            des = item.find('div', {'class': 'des hide'}).text.lstrip().rstrip()
            view = item.find('span', class_='so-icon watch-num').text.lstrip().rstrip()
            dan_mu = item.find('span', class_='so-icon hide').text.lstrip().rstrip()
            up_date = item.find('span', class_='so-icon time').text.lstrip().rstrip()
            up_zhu = item.find('a', {'class': 'up-name'}).text.lstrip().rstrip()

            dic['title'].append(title)
            dic['description'].append(des)
            dic['view count'].append(view)
            dic['danmu count'].append(dan_mu)
            dic['owner'].append(up_zhu)
            dic['date'].append(up_date)

        temp_df = pd.DataFrame(dic)
        return temp_df

    # go to the next page
    def next_page(self, page_num):
        next_page = page_num+1
        next_button = self.driver.find_element_by_xpath('//button[text()='+str(next_page)+']')
        ActionChains(self.driver).move_to_element(next_button).perform()
        next_button.click()
        
    #### data cleaning #########
    ############################

    def clean_data(self, df, *colnames):
        #df = df.drop(columns=['Unnamed: 0'])
        df = df.dropna(subset=['owner'])  # if owner == na, data not scraped properly, drop the row

        def numericalize(df, col):
            temp = []
            df[col].fillna('0', inplace=True)
            for i in list(df[col]):  # process the string-ish numerical terms
                if i[-1] == '万':
                    curr = int(float(i[:-1]) * 10000)
                    temp.append(curr)
                else:
                    temp.append(int(i))
            df.drop(columns=[col])
            df[col] = temp

        for col in colnames:
            numericalize(df, col)

        df = df[df['date'] >= '2018-08-02']  # change the date filtering here according to what you waht
        return df

if __name__ == '__main__':
    bilibili = Bilibili(keyword)
    bilibili.open_page()
    bilibili.search()
    res = bilibili.init_df()
    ## limit the number of pages here
    for i in range(1, 50):
        curr = bilibili.get_data()
        res = res.append(curr)
        print('done', i)
        bilibili.next_page(i)
    bilibili.get_driver().quit()
    
    # clean
    res = bilibili.clean_data(res, 'play_count', 'danmu_count')
    # write to csv
    res.to_csv('bilibili_result_%s.csv' % keyword, encoding='utf-8-sig')
