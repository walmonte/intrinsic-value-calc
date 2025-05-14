import csv
import logging
import os
import traceback

from utils import utils
from datetime import date
from service.DataService import DataService


CACHE_FILE = 'data/cache.csv'
LOGGER = logging.getLogger()


class Stock:
    def __init__(self, symbol, eps_next_5y=None):
        self.symbol = symbol.upper()
        self.name = None
        self.free_cash_flow = None
        self.cash = None
        self.total_debt = None
        self.outstanding_shares = None
        self.beta = None
        self.eps_next_5y = eps_next_5y
        self.current_price = None
        self.price_to_book = None
        self.fair_price = None
        self.present_value = None

        self.get_data(DataService())

    def get_data(self, data_service=None):
        if not self.get_data_from_csv():
            try:
                response = data_service.fetch_all_data(self.symbol)
                if response is None:
                    LOGGER.error(f"[{self.symbol}] Failed to fetch data from API.")
                    return
                else:
                    cash_flow = response['cash_flow']
                    balance_sheet = response['balance_sheet']
                    overview = response['overview']
                    global_quote = response['global_quote']

                op_cashflow = utils.safe_float(cash_flow['operatingCashflow'])
                capex = utils.safe_float(cash_flow['capitalExpenditures'])
                self.free_cash_flow = op_cashflow - capex

                self.cash = utils.safe_float(balance_sheet['cashAndShortTermInvestments'])
                self.total_debt = utils.safe_float(balance_sheet['shortLongTermDebtTotal'])

                self.name = overview['Name']
                self.price_to_book = utils.safe_float(overview['PriceToBookRatio'])
                self.beta = utils.safe_float(overview['Beta'])
                self.outstanding_shares = utils.safe_float(overview['SharesOutstanding'])

                self.current_price = utils.safe_float(global_quote['05. price'])
            except ValueError:
                print("ValueError: Could not convert data to float.")
                print(traceback.format_exc())
                LOGGER.error(f"[{self.symbol}] ValueError: Could not convert data to float. "
                              f"{traceback.format_exc()}")
                return
            except KeyError as err:
                print(f"{err}: missing key data point. Cancelling...")
                print(traceback.format_exc())
                LOGGER.error(f"[{self.symbol}] KeyError: missing key data point for {self.symbol}. "
                              f"Cancelling... {traceback.format_exc()}")
                return
            except BaseException as err:
                print(f"Unexpected {err=}, {type(err)=}")
                LOGGER.error(f"[{self.symbol}] Unexpected {err=}, {type(err)=}. Traceback: {traceback.format_exc()}")
                return

            self.compute_valuation()

    def compute_valuation(self):
        eps_6_to_10y = self.eps_next_5y / 2
        eps_10to_20y = 0.04
        wacc = float(utils.find_wacc(self.beta))

        discount_factor = 1 / (1 + wacc)
        discounted_cashflow = 0
        for i in range(1, 6):
            discounted_cashflow += self.free_cash_flow * (1 + self.eps_next_5y) ** i * discount_factor ** i

        cashflow_5y = self.free_cash_flow * (1 + self.eps_next_5y) ** 5
        for i in range(1, 6):
            discounted_cashflow += cashflow_5y * (1 + eps_6_to_10y) ** i * discount_factor ** (i + 5)

        cashflow_10y = cashflow_5y * (1 + eps_6_to_10y) ** 5
        for i in range(1, 11):
            discounted_cashflow += cashflow_10y * (1 + eps_10to_20y) ** i * discount_factor ** (i + 10)

        self.present_value = self.cash - self.total_debt + discounted_cashflow  # PV = present value
        self.fair_price = self.present_value / self.outstanding_shares

        self.save_data_to_csv()

    def get_data_from_csv(self):
        with open('data/date_of_last_cache.txt', mode='r', newline='', encoding='utf-8') as f:
            latest_cache = f.read()
            latest_cache = utils.parse_date(latest_cache)

        cache_is_too_old = (date.today() - latest_cache).days > 30
        if cache_is_too_old or (not os.path.isfile(CACHE_FILE)) or (os.path.getsize(CACHE_FILE) == 0):
            with open(CACHE_FILE, mode='w', newline='') as f:
                headers = ['symbol', 'name', 'fcc', 'cash', 'total_debt',
                           'shares', 'beta', 'eps_next_5y', 'current_price',
                           'fair_price', 'price_to_book', 'PV']
                writer = csv.writer(f)
                writer.writerow(headers)
            LOGGER.info("Cache file was over 30 days old, didn't exist or was empty. It was set to have headers only.")
            return False

        with open(CACHE_FILE, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            line_count = 0
            for row in csv_reader:
                if row['symbol'].upper() == self.symbol:
                    self.name = row['name']
                    self.free_cash_flow = float(row['fcc'])
                    self.cash = float(row['cash'])
                    self.total_debt = float(row['total_debt'])
                    self.outstanding_shares = float(row['shares'])
                    self.beta = float(row['beta'])
                    self.current_price = float(row['current_price'])
                    self.fair_price = float(row['fair_price'])
                    self.price_to_book = float(row['price_to_book'])
                    self.present_value = float(row['PV'])
                    LOGGER.info(f'Retrieved {self.symbol} from cache.csv.')
                    return True
                line_count += 1
        return False

    def save_data_to_csv(self):
        fields = [self.symbol, self.name, self.free_cash_flow, self.cash, self.total_debt,
                  self.outstanding_shares, self.beta, self.eps_next_5y, self.current_price,
                  self.fair_price, self.price_to_book, self.present_value]

        with open(CACHE_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(fields)

        with open('data/date_of_last_cache.txt', mode='w', newline='', encoding='utf-8') as f:
            f.write(str(date.today()))
            LOGGER.info('Updated date of last cache.')

    def get_as_row(self):
        try:
            row = [self.symbol,
                   self.name,
                   utils.format_currency(float(self.current_price * self.outstanding_shares)),
                   utils.format_currency(float(self.present_value)),
                   utils.format_currency(float(self.current_price)),
                   utils.format_currency(float(self.fair_price)),
                   '{:,.2f}'.format(float(self.price_to_book)),
                   '{:,.0f}%'.format(float(self.fair_price / self.current_price * 100))]
        except TypeError:
            row = [self.symbol, self.name, 'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a']
            LOGGER.warning(f'[{self.symbol}] TypeError when getting table row.')
        return row
