import logging
import requests
from src.utils import utils
from src.utils.api_function_enum import ApiFunction


LOGGER = logging.getLogger(__name__)


class DataService:
    """
    A service class to fetch stock data from the Alpha Vantage API.
    """

    def __init__(self):
        self.request_count = 0

    def fetch_data(self, func: ApiFunction, symbol: str):
        """
        Fetches data from the Alpha Vantage API for a given function and stock symbol.
        :param func: endpoint function to fetch data from.
        :param symbol: stock to fetch data for.
        :return: A JSON object containing the fetched data or None if the request fails.
        """
        function_name = func.get_json_name()
        url = func.get_url().format(symbol)
        LOGGER.info(
            "Fetching data for [%s] from '%s' endpoint...", symbol, function_name
        )

        if self.request_count == 74:
            utils.take_break()
            self.request_count = 0
        self.request_count += 1

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            LOGGER.warning(
                "Error fetching data from '%s' endpoint: %d",
                function_name,
                response.status_code,
            )
            return None

        data = response.json()
        if not data:
            LOGGER.warning(
                "Request was successful, but no data was returned. \
                Symbol [%s] is probably de-listed or traded over the counter.",
                symbol,
            )
            return None

        LOGGER.info("Request was successful")
        return data

    def fetch_all_data(self, symbol):
        """
        Fetches all relevant data for the given symbol from the Alpha Vantage API.
        :param symbol: The stock symbol to fetch data for.
        :return: A dictionary containing the fetched data or None if any data is missing.
        """
        data = {}
        for func in ApiFunction:
            response = self.fetch_data(func, symbol)
            if response is None or not isinstance(response, dict):
                continue
            match func:
                case ApiFunction.OVERVIEW:
                    data[func.get_json_name()] = response
                case ApiFunction.GLOBAL_QUOTE:
                    data[func.get_json_name()] = response["Global Quote"]
                case ApiFunction.EARNINGS:
                    data[func.get_json_name()] = response["annualEarnings"]
                case _:
                    data[func.get_json_name()] = response["annualReports"][0]

        if len(data) != len(ApiFunction):
            LOGGER.warning("Failed to fetch all necessary data for symbol: %s", symbol)
            return None

        return data
