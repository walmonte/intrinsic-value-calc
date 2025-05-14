from enum import Enum
import os


API_KEY = os.environ['ALPHA_VANTAGE_PREM_API_KEY']
BASE_URL = 'https://www.alphavantage.co/query?function={}&symbol={}&apikey=' + API_KEY


class ApiFunction(Enum):
    CASH_FLOW = ('CASH_FLOW', 'cash_flow')
    BALANCE_SHEET = ('BALANCE_SHEET', 'balance_sheet')
    OVERVIEW = ('OVERVIEW', 'overview')
    GLOBAL_QUOTE = ('GLOBAL_QUOTE', 'global_quote')

    def get_url(self):
        return BASE_URL.format(self.value[0], '{}')

    def get_url_name(self):
        return self.value[0]

    def get_json_name(self):
        return self.value[1]
