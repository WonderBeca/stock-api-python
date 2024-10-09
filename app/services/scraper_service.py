import httpx
import logging
from bs4 import BeautifulSoup
from app.schemas.stock_schema import StockCreate, StockValues, PerformanceData, Competitor
from fastapi import HTTPException
import re
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
import os


class MarketWacth():
    """
    A class to handle MarketWatch sessions and interactions, including optional proxy support.

    Attributes:
        email (str): The email used for logging into MarketWatch, sourced from environment variables.
        password (str): The password used for logging into MarketWatch, sourced from environment variables.
        client_id (str): The client ID used for MarketWatch, sourced from environment variables or default value.
        proxy (str): The proxy server address, if any, to route requests through.
        cookies (httpx.Cookies): The cookies associated with the session.
        session (httpx.Client): The HTTP client used for making requests to the MarketWatch service.

    Args:
        proxy (str, optional): The proxy server address. Default is an empty string, meaning no proxy is used.
        skip_login (bool, optional): If True, skip the login process. Default is False.

    Methods:
        create_session(): Initializes and returns an HTTP client session with appropriate headers and proxy settings.

    Raises:
        httpx.HTTPError: If the proxy test request fails.
    """
    def __init__(self, proxy: str = "", skip_login: bool = False):
        self.email = os.getenv('MARKETWATCH_USER')
        self.password = os.getenv('MARKETWATCH_PWD')
        self.client_id = os.getenv('MARKETWATCH_ID', '5hssEAdMy0mJTICnJNvC9TXEw3Va7jfO')
        self.proxy = proxy
        self.cookies = httpx.Cookies()
        self.session = self.create_session()

    def create_session(self):
        """
        Initializes an HTTP client session with specified headers and proxy settings.

        Returns:
            httpx.Client: The configured HTTP client session.

        Raises:
            httpx.HTTPError: If the proxy test request fails.
        """
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
                logging.warning(f"Proxy {self.proxy} is working. Status code: {response.status_code}")
                logging.warning("Response content:", response.json())
            except httpx.HTTPError as e:
                logging.erorr(f"Failed to test proxy: {e}")

        return client

    def parse_market_cap(self, market_cap_str):
        """
        Parse a market capitalization string into its currency and float value.

        The input string can represent market capitalizations in various formats,
        such as "$3.09T", "₩403.65T", or "¥50M". The method will convert these
        representations into a numeric float value and identify the currency symbol.

        Args:
            market_cap_str (str): The market capitalization string to parse,
                which may include currency symbols and suffixes indicating scale
                (T for trillion, B for billion, M for million).

        Returns:
            tuple: A tuple containing:
                - currency (str): The currency symbol extracted from the input string,
                defaulting to '$' if no specific currency is found.
                - value (float): The numeric value representing the market capitalization
                in the corresponding currency.

        Examples:
            >>> parse_market_cap("$3.09T")
            ('$','3090000000000.0')

            >>> parse_market_cap("₩403.65B")
            ('$','403650000000.0')

            >>> parse_market_cap("¥50M")
            ('$','50000000.0')

            >>> parse_market_cap("100")
            ('$','100.0')

        Note:
            If the input string does not end with a recognized suffix, it will
            be treated as a direct float value.
        """
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
            value = float(market_cap_str)
            currency = '$'

        return currency, value

    def parse_competitors(self, soup):
        """
        Parse a BeautifulSoup object to extract competitor information.

        This method looks for a specific section in the provided HTML soup
        that contains competitor data in a table format. It extracts each
        competitor's name and market capitalization, and returns a list of
        dictionaries representing each competitor.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the
                parsed HTML content of a webpage containing competitor information.

        Returns:
            list: A list of dictionaries, where each dictionary contains:
                - name (str): The name of the competitor.
                - market_cap (dict): A dictionary with the market capitalization
                of the competitor, including:
                    - currency (str): The currency symbol of the market cap.
                    - value (float): The numeric value of the market cap.

        Examples:
            >>> competitors_list = parse_competitors(soup)
            >>> print(competitors_list)
            [{'name': 'Company A', 'market_cap': {'currency': '$', 'value': 1000000000.0}},
            {'name': 'Company B', 'market_cap': {'currency': '¥', 'value': 5000000000.0}}]

        Note:
            This method requires that the input HTML contains a specific structure
            for competitor data; if the structure changes, this method may need
            to be updated accordingly.
        """
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
        """
        Parse stock values from a BeautifulSoup object representing the
        HTML content of a stock market page.

        This method extracts key stock data, including the opening price,
        day range (low and high), and previous close value from the given
        HTML soup. It looks for specific sections within the soup to gather
        the required information.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the
                parsed HTML content of a stock market webpage.

        Returns:
            dict: A dictionary containing key stock values, including:
                - open (float): The opening price of the stock.
                - low (float): The lowest price of the stock during the day.
                - high (float): The highest price of the stock during the day.
                - close (float): The previous closing price of the stock.

        Examples:
            >>> stock_data = parse_stock_values(soup)
            >>> print(stock_data)
            {'open': 150.25, 'low': 148.00, 'high': 155.50, 'close': 149.75}

        Note:
            The method assumes a specific HTML structure for the stock data.
            If the structure of the webpage changes, the method may need to
            be updated accordingly.
        """
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
        """
        Parse performance data from a BeautifulSoup object representing the
        HTML content of a stock market page.

        This method extracts performance metrics over different time periods
        (5 days, 1 month, 3 months, year-to-date, and 1 year) from the
        given HTML soup. It looks for a specific performance table and
        collects the corresponding values for each period.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the
                parsed HTML content of a stock market webpage.

        Returns:
            dict: A dictionary containing performance metrics with the
                following keys:
                - five_days (float): The performance over the last 5 days.
                - one_month (float): The performance over the last month.
                - three_months (float): The performance over the last 3 months.
                - year_to_date (float): The year-to-date performance.
                - one_year (float): The performance over the last year.

        Examples:
            >>> performance_data = parse_performance_data(soup)
            >>> print(performance_data)
            {'five_days': 2.5, 'one_month': 3.1, 'three_months': 5.4, 'year_to_date': 12.0, 'one_year': 20.3}

        Note:
            The method assumes a specific HTML structure for the performance data.
            If the structure of the webpage changes, the method may need to
            be updated accordingly.
        """
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
        Scrape stock data from MarketWatch for a given stock symbol.

        This method constructs a URL for the specified stock symbol,
        sends a GET request to the MarketWatch website, and parses the
        HTML response to extract relevant information such as the
        company name, performance data, stock values, and competitors.

        Args:
            stock (str): The stock symbol to retrieve data for (e.g., 'AAPL' for Apple).

        Returns:
            dict: A dictionary containing the retrieved stock data, structured as follows:
                - status (int): HTTP status code (200 if successful).
                - message (str): A message indicating the success of the operation.
                - data (dict): Contains the following keys:
                    - company_name (str): The name of the company.
                    - performance_data (dict): A dictionary containing performance metrics.
                    - competitors (list): A list of competitors, where each competitor is
                    represented as a dictionary containing their name and market cap.
                    - stock_values (dict): A dictionary containing stock values, including
                    open, high, low, and close prices.
                    - company_code (str): The stock symbol.

        Raises:
            HTTPException: If the HTTP request fails or returns a status code
            other than 200, an HTTPException is raised with the corresponding
            status code and error message.

        Examples:
            >>> stock_info = scrape_marketwatch_data('AAPL')
            >>> print(stock_info['data']['company_name'])
            Apple Inc.

        Note:
            Ensure that the provided stock symbol is valid and exists on
            MarketWatch to avoid errors during scraping.
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
        """
        Map MarketWatch data to a StockCreate object.

        This method takes a dictionary containing MarketWatch data,
        extracts relevant stock values, performance data, and competitors,
        and constructs a StockCreate object containing all this information.

        Args:
            marketwatch_data (dict): A dictionary containing data from
                MarketWatch. It should have the following structure:
                - stock_values (dict): Contains stock values with keys:
                    - Open (float): The opening price of the stock.
                    - high (float): The highest price of the stock.
                    - low (float): The lowest price of the stock.
                    - close (float): The closing price of the stock.
                - performance_data (dict): Contains performance metrics
                for different periods:
                    - five_days (float): Performance over the last 5 days.
                    - one_month (float): Performance over the last month.
                    - three_months (float): Performance over the last 3 months.
                    - year_to_date (float): Year-to-date performance.
                    - one_year (float): Performance over the last year.
                - competitors (list): A list of competitor dictionaries,
                where each dictionary should contain:
                    - name (str): The name of the competitor.
                    - market_cap (dict): A dictionary with keys 'currency'
                    and 'value' representing the market cap.
                - company_code (str): The stock's company code.
                - company_name (str): The name of the company.

        Returns:
            StockCreate: An instance of StockCreate containing the company's
            stock data, including its code, name, stock values, performance
            metrics, and competitors.

        Examples:
            >>> marketwatch_data = {
                    'stock_values': {
                        'Open': 100.50,
                        'high': 110.00,
                        'low': 95.00,
                        'close': 105.25
                    },
                    'performance_data': {
                        'five_days': 2.5,
                        'one_month': 3.1,
                        'three_months': 5.4,
                        'year_to_date': 12.0,
                        'one_year': 20.3
                    },
                    'competitors': [
                        {'name': 'Competitor A', 'market_cap': {'currency': '$', 'value': 500000000}},
                        {'name': 'Competitor B', 'market_cap': {'currency': '$', 'value': 600000000}}
                    ],
                    'company_code': 'ABC',
                    'company_name': 'Company ABC'
                }
            >>> stock_data = map_marketwatch_data_to_stock_create(marketwatch_data)
            >>> print(stock_data)
            StockCreate(company_code='ABC', company_name='Company ABC', ...)

        Note:
            Ensure that the input dictionary follows the specified structure
            to avoid KeyError exceptions during extraction.
        """
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
