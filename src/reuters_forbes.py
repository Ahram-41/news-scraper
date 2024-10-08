import json
import time
import pandas as pd
from abc import ABC, abstractmethod
from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

class Scraper(ABC):
    def __init__(self, chrome_port='127.0.0.1:9226'):
        self.chrome_port = chrome_port
        self.page = None

    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def get_detail(self):
        pass

    @abstractmethod
    def save_data(self):
        pass

    def _init_page(self):
        self.page = ChromiumPage(self.chrome_port)

    def _save_to_json(self, data, filename):
        with open(filename, 'a', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write(',\n')

    def _load_json(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.loads('[' + f.read().rstrip(',\n') + ']')

class ReutersScraper(Scraper):
    def __init__(self, chrome_port='127.0.0.1:9226'):
        super().__init__(chrome_port)
        self.url = 'https://www.reuters.com/business/'

    def get_data(self):
        self._init_page()
        self.page.get(self.url)
        time.sleep(3)

        data_list = []

        while True:
            self.page.scroll.to_bottom()
            time.sleep(1)

            load_more_button_xpath = '//*[@class="button__button__2Ecqi button__secondary__18moI button__round__1nYLA button__w_auto__6WYRo text-button__container__3q3zX"]'
            self.page.ele(f'x:{load_more_button_xpath}').click()

            time.sleep(4)

            soup = BeautifulSoup(self.page.html, 'lxml')
            soup_items = soup.select('.story-collection__list-item__j4SQe')

            for item in soup_items:
                article_url = 'https://www.reuters.com' + item.select('a')[0]['href']
                data = {'url': article_url}

                if data not in data_list:
                    data_list.append(data)
                    print(data)
                    self._save_to_json(data, 'reuters_list.json')

            if len(data_list) >= 210:
                break

    def get_detail(self):
        self._init_page()
        data_list = self._load_json('reuters_list.json')

        for data in data_list:
            article_url = data.get('url')
            print(article_url)
            self.page.get(article_url)
            time.sleep(3)

            soup = BeautifulSoup(self.page.html, 'lxml')
            
            data['title'] = soup.select_one('h1').text.strip()
            data['author'] = soup.select_one('.text__medium__1kbOh.text__tag_label__6ajML').text.replace('By', '').strip()
            data['date'] = ' '.join([st.text for st in soup.select('.date-line__date___kNbY')])
            data['content'] = soup.select_one('.article-body__wrapper__3IxHM').text.strip()
            
            print(data)
            self._save_to_json(data, 'reuters_data.json')

    def save_data(self):
        data_list = self._load_json('reuters_data.json')
        df = pd.DataFrame(data_list)
        df.to_excel('reuters_data.xlsx', index=False)

class ForbesScraper(Scraper):
    def __init__(self, chrome_port='127.0.0.1:9226'):
        super().__init__(chrome_port)
        self.url = 'https://www.forbes.com/business/?sh=74da965e535f'

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('detach', True)
        options.add_argument('--no-sandbox')
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values': {
                'images': 2
            }
        })
        return webdriver.Chrome(options=options)

    def get_data(self):
        driver = self._init_driver()
        driver.get(self.url)
        time.sleep(3)

        while True:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            soup_list = soup.select('._4g0BEaLU')
            print(f"Number of articles found: {len(soup_list)}")
            
            if len(soup_list) >= 200:
                break

            try:
                load_more_button = driver.find_element(By.XPATH, '//*[@class="_18BedXz4 iWceBwQC Sn26m-xQ st6yY9Jv"]')
                driver.execute_script("arguments[0].scrollIntoView(false);", load_more_button)
                time.sleep(3)
                load_more_button.click()
                time.sleep(3)
            except Exception as e:
                print(f"Error encountered: {e}")
                break

        soup = BeautifulSoup(driver.page_source, 'lxml')
        soup_list = soup.select('._4g0BEaLU')
        
        for i, item in enumerate(soup_list[:200]):
            data = {
                'title': item.select_one('._1-FLFW4R').text.strip(),
                'author': item.select_one('._4tin10wS').text.strip(),
                'url': item.select_one('._1-FLFW4R')['href']
            }
            
            print(data)
            self._save_to_json(data, 'forbes_list.json')

        driver.quit()

    def get_detail(self):
        driver = self._init_driver()
        data_list = self._load_json('forbes_list.json')

        for data in data_list:
            url = data.get('url')
            print(f"Processing URL: {url}")
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'lxml')

            info = data

            try:
                info['time'] = soup.select_one('.content-data.metrics-text.color-body.light-text').text.strip()
            except:
                info['time'] = soup.select_one('.ycHdAQ4U._0th4g').text.strip()

            try:
                article_text = soup.select_one('.fs-article.fs-responsive-text.current-article').text.strip()
                sharing_text = soup.select_one('.article-sharing').text if soup.select_one('.article-sharing') else ''
                info['content'] = article_text.replace(sharing_text, '').strip()
            except:
                info['content'] = soup.select_one('.fs-article.fs-responsive-text.current-article').text.strip()

            print(info)
            self._save_to_json(info, 'forbes_data.json')

        driver.quit()

    def save_data(self):
        data_list = self._load_json('forbes_data.json')
        df = pd.DataFrame(data_list)
        df.to_excel('forbes_data.xlsx', index=False, encoding='utf-8-sig')

def main():
    reuters_scraper = ReutersScraper()
    forbes_scraper = ForbesScraper()

    # Reuters scraping
    reuters_scraper.get_data()
    reuters_scraper.get_detail()
    reuters_scraper.save_data()

    # Forbes scraping
    forbes_scraper.get_data()
    forbes_scraper.get_detail()
    forbes_scraper.save_data()

if __name__ == '__main__':
    main()