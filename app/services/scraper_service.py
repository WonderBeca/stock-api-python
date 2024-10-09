import httpx
from bs4 import BeautifulSoup
from app.schemas.stock_schema import StockCreate, StockValues, PerformanceData, Competitor
from fastapi import HTTPException
import re
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
import os


class MarketWacth():
    def __init__(self, proxy: str = "", skip_login: bool = False):
        """
        Initialize the MarketWatch API

        :param email: Email
        :param password: Password
        :param proxy: Proxy URL (optional)
        :param skip_login: If True, skip the login process (useful for certain non-authenticated calls).
        """
        self.email = os.getenv('MARKETWATCH_USER')
        self.password = os.getenv('MARKETWATCH_PWD')
        self.client_id = os.getenv('MARKETWATCH_ID', '5hssEAdMy0mJTICnJNvC9TXEw3Va7jfO')
        self.proxy = proxy
        self.cookies = httpx.Cookies()
        self.session = self.create_session()

    def create_session(self):
        inconspicuous_user = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/"
        }

        if self.proxy == "":
            client = httpx.Client(headers=inconspicuous_user, cookies=self.cookies, follow_redirects=False)
        else:
            proxies = {
                "http://": httpx.HTTPTransport(proxy=self.proxy),
                "https://": httpx.HTTPTransport(proxy=self.proxy),
            } if self.proxy != "" else {}
            client = httpx.Client(
                headers=inconspicuous_user, cookies=self.cookies, follow_redirects=False, mounts=proxies)
            # test proxy
            try:
                response = client.get("https://httpbin.org/ip")
                response.raise_for_status()
                print(f"Proxy {self.proxy} is working. Status code: {response.status_code}")
                print("Response content:", response.json())
            except httpx.HTTPError as e:
                raise Exception(f"Failed to test proxy: {e}") from e

        return client

    def parse_market_cap(self, market_cap_str):
        # Parse a string like "$3.09T" or "₩403.65T" to return the currency and a float value
        market_cap_str = market_cap_str.replace('$', '').replace('₩', '').replace('¥', '').strip()

        if market_cap_str[-1] == 'T':
            value = float(market_cap_str[:-1]) * 1_000_000_000_000
            currency = '$'
        elif market_cap_str[-1] == 'B':
            value = float(market_cap_str[:-1]) * 1_000_000_000
            currency = '$'
        elif market_cap_str[-1] == 'M':
            value = float(market_cap_str[:-1]) * 1_000_000
            currency = '$'
        else:
            value = float(market_cap_str)  # Valor normal
            currency = '$'

        return currency, value

    def parse_competitors(self, soup):
        competitors = []
        competitor_header = soup.find('div', class_='element element--table overflow--table Competitors')

        if competitor_header:
            table = competitor_header.find('table', class_='table table--primary align--right')
            tbody = table.find('tbody', class_='table__body')

            for row in tbody.find_all('tr', class_='table__row'):
                name_cell = row.find('td', class_='table__cell w50')
                market_cap_cell = row.find('td', class_='table__cell w25 number')
                currency, value = self.parse_market_cap(market_cap_cell.text.strip())
                competitor = {
                    'name': name_cell.text.strip(),
                    'market_cap': {
                        'currency': currency,
                        'value': value
                    }
                }
                competitors.append(competitor)

        return competitors

    def parse_stock_values(self, soup):
        key_data_header = soup.find('span', class_='label', text='Key Data')
        if key_data_header:
            key_data_list = key_data_header.find_parent(
                'div', class_='element--list').find_all('li', class_='kv__item')

            key_data = {}
            for item in key_data_list:
                label = item.find('small', class_='label').text.strip()
                value = item.find('span', class_='primary').text.strip()
                if label == 'Open':
                    value = re.sub(r'[^\d.]', '', value)
                    open_value = value.replace('$', '').replace(',', '')
                    key_data['open'] = float(open_value)
                elif label == 'Day Range':
                    day_range = value.replace(',', '').split(' - ')
                    key_data['low'] = float(day_range[0])
                    key_data['high'] = float(day_range[1])

        close_table = soup.find('div', class_='intraday__close').find('table')
        if close_table:
            previous_close_value = close_table.find('td', class_='table__cell u-semi').text.strip()
            close_value = previous_close_value.replace('$', '').replace(',', '')
            close_value = re.sub(r'[^\d.]', '', close_value)
            key_data['close'] = float(close_value)

        return key_data

    def parse_performance_data(self, soup):
        performance_table = soup.find("div", class_="element element--table performance")
        rows = performance_table.find_all("tr", class_="table__row")
        performance_data = {}
        for row in rows:
            period = row.find("td", class_="table__cell").text.strip()
            value = row.find("li", class_="content__item value ignore-color").text.strip().replace('%', '')

            if "5 Day" in period:
                performance_data['five_days'] = float(value)
            elif "1 Month" in period:
                performance_data['one_month'] = float(value)
            elif "3 Month" in period:
                performance_data['three_months'] = float(value)
            elif "YTD" in period:
                performance_data['year_to_date'] = float(value)
            elif "1 Year" in period:
                performance_data['one_year'] = float(value)

        return performance_data

    def scrape_marketwatch_data(self, stock):
        """
        Scrape stock data from MarketWatch for a given stock.

        Args:
            stock (str): The stock code to scrape data for.

        Raises:
            HTTPException: If stock data cannot be retrieved or stock is not found.

        Returns:
            dict: A dictionary containing stock information.
        """
        url = f"https://www.marketwatch.com/investing/stock/{stock}"
        response = self.session.get(url, follow_redirects=True)

        if response.status_code != 200:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve stock data. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        company_name = soup.find("h1", class_="company__name")

        if not company_name:
            return None

        performance = self.parse_performance_data(soup)
        stock_values = self.parse_stock_values(soup)
        competitors = self.parse_competitors(soup)

        stock_info = {
            'status': HTTP_200_OK,
            'message': 'Stock data retrieved successfully',
            'data': {
                'company_name': company_name.text.strip(),
                'performance_data': performance,
                'competitors': competitors,
                'stock_values': stock_values,
                'company_code': stock
            }
        }
        return stock_info

    def map_marketwatch_data_to_stock_create(self, marketwatch_data):
        stock_values = StockValues(
            open=marketwatch_data['stock_values']['Open'],
            high=marketwatch_data['stock_values']['high'],
            low=marketwatch_data['stock_values']['low'],
            close=marketwatch_data['stock_values']['close']
        )

        performance_data = PerformanceData(
            five_days=marketwatch_data['performance_data']['five_days'],
            one_month=marketwatch_data['performance_data']['one_month'],
            three_months=marketwatch_data['performance_data']['three_months'],
            year_to_date=marketwatch_data['performance_data']['year_to_date'],
            one_year=marketwatch_data['performance_data']['one_year'],
        )

        competitors = [
            Competitor(
                name=comp['name'],
                market_cap=comp['market_cap']
            )
            for comp in marketwatch_data['competitors']
        ]

        return StockCreate(
            company_code=marketwatch_data['company_code'],
            company_name=marketwatch_data['company_name'],
            stock_values=stock_values,
            performance_data=performance_data,
            competitors=competitors
        )
