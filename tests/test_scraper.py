import unittest
from bs4 import BeautifulSoup
from unittest.mock import patch

from app.services.scraper_service import MarketWacth


class TestMarketWatch(unittest.TestCase):

    @patch.object(MarketWacth, '__init__', lambda x: None) 
    def setUp(self):
        with patch('app.services.scraper_service.httpx') as mock_httpx:
            self.marketwatch = MarketWacth()
            self.mock_httpx = mock_httpx

    def test_parse_market_cap(self):
        self.assertEqual(self.marketwatch.parse_market_cap("$3.09T"), ('$', 3090000000000.0))
        self.assertEqual(self.marketwatch.parse_market_cap("₩403.65B"), ('$', 403650000000.0))
        self.assertEqual(self.marketwatch.parse_market_cap("¥50M"), ('$', 50000000.0))
        self.assertEqual(self.marketwatch.parse_market_cap("100"), ('$', 100.0))

    def test_parse_competitors(self):
        html = """
        <div class="element element--table overflow--table Competitors">
            <table class="table table--primary align--right">
                <tbody class="table__body">
                    <tr class="table__row">
                        <td class="table__cell w50">Company A</td>
                        <td class="table__cell w25 number">₩500M</td>
                    </tr>
                    <tr class="table__row">
                        <td class="table__cell w50">Company B</td>
                        <td class="table__cell w25 number">$1B</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        competitors = self.marketwatch.parse_competitors(soup)
        expected = [
            {'name': 'Company A', 'market_cap': {'currency': '$', 'value': 500000000.0}},
            {'name': 'Company B', 'market_cap': {'currency': '$', 'value': 1000000000.0}}
        ]
        self.assertEqual(competitors, expected)

    def test_parse_stock_values(self):
        html = """
        <div class="element element--list">
            <header class="header header--secondary">
                <h2 class="title">
                    <span class="label">Key Data</span>
                </h2>
            </header>
            <ul class="list list--kv list--col50">
                <li class="kv__item">
                    <small class="label">Open</small>
                    <span class="primary">427.00p</span>
                    <span class="secondary no-value"></span>
                </li>
                <li class="kv__item">
                    <small class="label">Day Range</small>
                    <span class="primary">415.00 - 434.54</span>
                    <span class="secondary no-value"></span>
                </li>
            </ul>
        </div>
        <div class="intraday__close">
            <table>
                <tr>
                    <td class="table__cell u-semi">$149.75</td>
                </tr>
            </table>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        print(soup)
        stock_values = self.marketwatch.parse_stock_values(soup)
        expected = {'open': 427.00, 'low': 415.00, 'high': 434.54, 'close': 149.75}  # Atualizar conforme necessário
        self.assertEqual(stock_values, expected)

    def test_parse_performance_data(self):
        html = """
        <div class="element element--table performance">
            <tr class="table__row">
                <td class="table__cell">5 Day</td>
                <li class="content__item value ignore-color">2.5%</li>
            </tr>
            <tr class="table__row">
                <td class="table__cell">1 Month</td>
                <li class="content__item value ignore-color">3.1%</li>
            </tr>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        performance_data = self.marketwatch.parse_performance_data(soup)
        expected = {'five_days': 2.5, 'one_month': 3.1}
        self.assertEqual(performance_data, expected)
