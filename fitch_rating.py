import json
import time
import pandas as pd
from typing import List, Dict, Any
from selenium import webdriver
from bs4 import BeautifulSoup

class FitchRatingsScraper:
    """
    A web scraper for extracting ratings data from Fitch Ratings.

    Attributes:
        company_file (str): The path to the JSON file containing the list of companies to search.
        output_file (str): The path to the output JSON file where scraped data will be stored.
        driver (webdriver.Chrome): The Selenium web driver used for navigating web pages.
    """

    def __init__(self, company_file: str, output_file: str) -> None:
        """
        Initializes the scraper with the input company file and output file paths.
        """
        self.company_file = company_file
        self.output_file = output_file
        self.driver = self._init_driver()

    def _init_driver(self) -> webdriver.Chrome:
        """
        Initializes and configures the Selenium web driver.
        """
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('detach', True)
        options.add_argument('--no-sandbox')
        return webdriver.Chrome(options=options)

    def _load_company_list(self) -> List[str]:
        """
        Loads the list of companies from the specified JSON file.
        """
        with open(self.company_file, 'r', encoding='utf-8') as f:
            json_str = f.read()
        data_json = '[' + json_str[0:-2] + ']'
        return json.loads(data_json)

    def _save_data(self, data: Dict[str, Any]) -> None:
        """
        Saves a dictionary of data to the output JSON file.
        """
        with open(self.output_file, 'a', encoding='utf8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + ',\n')

    def scrape_company_data(self) -> None:
        """
        Main method that controls the scraping process for each company in the list.
        """
        company_list = self._load_company_list()
        
        for company in company_list:
            url = self._build_search_url(company)
            print(f"Scraping URL: {url}")
            self.driver.get(url)
            time.sleep(5)

            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            data = self._extract_data(soup, company)
            self._save_data(data)

    def _build_search_url(self, company_name: str) -> str:
        """
        Constructs the search URL for a given company name.
        """
        return 'https://www.fitchratings.com/search/?query=' + '%20'.join(company_name.split(' '))

    def _extract_data(self, soup: BeautifulSoup, company_name: str) -> Dict[str, Any]:
        """
        Extracts ratings data from the HTML content of the page.
        """
        data = {'keyword': company_name}

        if len(soup.select('.heading--2')) >= 1 and 'Sorry, no results.' in soup.select('.heading--2')[0].text:
            print(data)
            return data

        data['title'] = soup.select('.page-layout.page-layout--2__left-main.content .heading--5 a')[0].text.strip()
        data['url'] = 'https://www.fitchratings.com' + soup.select('.page-layout.page-layout--2__left-main.content .heading--5 a')[0].attrs['href']

        print(f"Extracted URL: {data['url']}")
        self.driver.get(data['url'])
        time.sleep(5)
        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        tr_list = soup.select('.table.table--1 .table__wrapper tbody tr')
        if not tr_list:
            print(data)
            return data

        for tr in tr_list:
            info = {
                'keyword': data['keyword'],
                'title': data['title'],
                'url': data['url'],
                'RATING': tr.select('td')[0].text.strip(),
                'ACTION': tr.select('td')[1].text.strip(),
                'DATE': tr.select('td')[2].text.strip(),
                'TYPE': tr.select('td')[3].text.strip(),
            }
            print(info)
            self._save_data(info)

        return data

    def save_to_excel(self) -> None:
        """
        Converts the JSON data from the output file into an Excel spreadsheet.
        """
        with open(self.output_file, 'r', encoding='utf-8') as f:
            json_str = f.read()
        data_json = '[' + json_str[0:-2] + ']'
        data_list = json.loads(data_json)

        df = pd.DataFrame(data_list)
        df.to_excel('data.xlsx', index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    scraper = FitchRatingsScraper(company_file='company_name3.json', output_file='list.json')
    scraper.scrape_company_data()
    scraper.save_to_excel()
