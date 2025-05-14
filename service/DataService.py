import logging
import requests
from utils import utils
from utils.ApiFunction import ApiFunction


LOGGER = logging.getLogger()


class DataService:
    """
    A service class to fetch stock data from the Alpha Vantage API.
    """

    def __init__(self):
        self.request_count = 0

    def fetch_data(self, url):
        """
        Fetches data from the given URL and returns the JSON response.
        :param url: The URL to fetch data from.
        :return: The JSON response or None if the response is empty or contains an error.
        """
        try:
            LOGGER.info(f"Fetching data from URL: {url}")
            if self.request_count == 74:
                self.request_count = 0
                utils.take_break()
            self.request_count += 1

            response = requests.get(url)
            data = response.json()
            if 'Note' in data or not data:
                LOGGER.error("Bad response due to API limits or empty response.")
                return None
            return data
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Request failed: {e}")
            return None

    def fetch_all_data(self, symbol):
        """
        Fetches all relevant data for the given symbol from the Alpha Vantage API.
        :param symbol: The stock symbol to fetch data for.
        :return: A dictionary containing the fetched data or None if any data is missing.
        """
        data = {}
        for func in ApiFunction:
            match func:
                case ApiFunction.OVERVIEW:
                    data[func.get_json_name()] = self.fetch_data(func.get_url().format(symbol))
                case ApiFunction.GLOBAL_QUOTE:
                    data[func.get_json_name()] = self.fetch_data(func.get_url().format(symbol))['Global Quote']
                case _:
                    data[func.get_json_name()] = self.fetch_data(func.get_url().format(symbol))['annualReports'][0]

        if any(value is None for value in data.values()):
            LOGGER.error(f"Failed to fetch all data for symbol: {symbol}")
            return None

        return data
