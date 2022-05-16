import csv
import logging
import os
import traceback
import requests
import my_utils

CACHE_FILE = 'data/cache.csv'
LOG_FORMAT = '[%(asctime)s] %(process)d - %(levelname)s - %(message)s'

logging.basicConfig(filename=f'logs/{my_utils.get_todays_date()}.log', filemode='a', format=LOG_FORMAT,
                    datefmt='%d-%b-%y %H:%M:%S')


def safe_float(i):
    if i == 'None':
        return 0.0
    return float(i)


class Stock:
    req_count = 0

    def __init__(self, symbol, eps_next_5y=None):
        self.symbol = symbol.upper()
        self.name = None
        self.fcc = None
        self.cash = None
        self.total_debt = None
        self.shares = None
        self.beta = None
        self.eps_next_5y = eps_next_5y
        self.current_price = None
        self.price_to_book = None
        self.fair_price = None
        self.PV = None

        self.get_data()

    def get_data(self):
        if not self.get_data_from_csv():
            if Stock.req_count > 0 and Stock.req_count % 4 == 0:  # take a break every 4 requests
                my_utils.take_break()

            Stock.req_count += 4
            try:
                # get cash flow statement -> extract operatingCashflow and capex
                full_url = my_utils.build_url('CASH_FLOW', self.symbol)
                r = requests.get(full_url).json()
                if my_utils.bad_response(r):
                    return
                op_cashflow = safe_float(r['annualReports'][0]['operatingCashflow'])
                capex = safe_float(r['annualReports'][0]['capitalExpenditures'])
                self.fcc = op_cashflow - capex

                # get current cash, total debt
                full_url = my_utils.build_url('BALANCE_SHEET', self.symbol)
                r = requests.get(full_url).json()
                if my_utils.bad_response(r):
                    return
                self.cash = safe_float(r['annualReports'][0]['cashAndShortTermInvestments'])
                self.total_debt = safe_float(r['annualReports'][0]['shortLongTermDebtTotal'])

                # get beta and outstanding shares
                full_url = my_utils.build_url('OVERVIEW', self.symbol)
                r = requests.get(full_url).json()
                if my_utils.bad_response(r):
                    return

                self.name = r['Name']
                self.price_to_book = safe_float(r['PriceToBookRatio'])
                self.beta = safe_float(r['Beta'])
                self.shares = safe_float(r['SharesOutstanding'])

                # get quote
                full_url = my_utils.build_url('GLOBAL_QUOTE', self.symbol)
                r = requests.get(full_url).json()
                if my_utils.bad_response(r):
                    return

                self.current_price = safe_float(r['Global Quote']['05. price'])
            except ValueError:
                print("ValueError: Could not convert data to float.")
                print(traceback.format_exc())
                logging.error(f"[{self.symbol}] ValueError: Could not convert data to float. "
                              f"{traceback.format_exc()}")
                return
            except KeyError as err:
                print(f"{err}: missing key data point. Cancelling...")
                print(traceback.format_exc())
                logging.error(f"[{self.symbol}] KeyError: missing key data point for {self.symbol}. "
                              f"Cancelling... {traceback.format_exc()}")
                return
            except BaseException as err:
                print(f"Unexpected {err=}, {type(err)=}")
                logging.error(f"[{self.symbol}] Unexpected {err=}, {type(err)=}. Traceback: {traceback.format_exc()}")
                return

            self.compute_valuation()

    def get_data_from_csv(self):
        with open('data/date_of_last_cache.txt', mode='r', newline='', encoding='utf-8') as f:
            latest_cache = f.read()
            latest_cache = my_utils.parse_date(latest_cache)

        cache_is_too_old = (my_utils.get_todays_date() - latest_cache).days > 30
        if cache_is_too_old or not os.path.isfile(CACHE_FILE) or (os.path.getsize(CACHE_FILE) == 0):
            with open(CACHE_FILE, mode='w', newline='') as f:
                headers = ['symbol', 'name', 'fcc', 'cash', 'total_debt',
                           'shares', 'beta', 'eps_next_5y', 'current_price',
                           'fair_price', 'price_to_book', 'PV']
                writer = csv.writer(f)
                writer.writerow(headers)
            logging.info('Cache file was over 30 days old, doesn\'t exist or is empty. It was successfully cleaned.')
            return False

        with open(CACHE_FILE, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            line_count = 0
            for row in csv_reader:
                if row['symbol'].upper() == self.symbol:
                    self.name = row['name']
                    self.fcc = float(row['fcc'])
                    self.cash = float(row['cash'])
                    self.total_debt = float(row['total_debt'])
                    self.shares = float(row['shares'])
                    self.beta = float(row['beta'])
                    self.current_price = float(row['current_price'])
                    self.fair_price = float(row['fair_price'])
                    self.price_to_book = float(row['price_to_book'])
                    self.PV = float(row['PV'])
                    logging.info(f'Retrieved {self.symbol} from cache.csv.')
                    return True
                line_count += 1
        return False

    def compute_valuation(self):
        eps_6_to_10y = self.eps_next_5y / 2
        eps_10to_20y = 0.04
        wacc = float(my_utils.find_wacc(self.beta))

        discount_factor = 1 / (1 + wacc)
        discounted_cashflow = 0
        for i in range(1, 6):
            discounted_cashflow += self.fcc * (1 + self.eps_next_5y) ** i * discount_factor ** i

        cashflow_5y = self.fcc * (1 + self.eps_next_5y) ** 5
        for i in range(1, 6):
            discounted_cashflow += cashflow_5y * (1 + eps_6_to_10y) ** i * discount_factor ** (i + 5)

        cashflow_10y = cashflow_5y * (1 + eps_6_to_10y) ** 5
        for i in range(1, 11):
            discounted_cashflow += cashflow_10y * (1 + eps_10to_20y) ** i * discount_factor ** (i + 10)

        self.PV = self.cash - self.total_debt + discounted_cashflow  # PV = present value
        self.fair_price = self.PV / self.shares

        self.save_data_to_csv()

    def save_data_to_csv(self):
        fields = [self.symbol, self.name, self.fcc, self.cash, self.total_debt,
                  self.shares, self.beta, self.eps_next_5y, self.current_price,
                  self.fair_price, self.price_to_book, self.PV]

        with open(CACHE_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(fields)

        with open('data/date_of_last_cache.txt', mode='w', newline='', encoding='utf-8') as f:
            f.write(str(my_utils.get_todays_date()))
            logging.info('Updated date of last cache.')

    def get_as_row(self):
        try:
            row = [self.symbol,
                   self.name,
                   '{:,.2f}'.format(float(self.current_price * self.shares)),
                   '{:,.2f}'.format(float(self.PV)),
                   '{:,.2f}'.format(float(self.current_price)),
                   '{:,.2f}'.format(float(self.fair_price)),
                   '{:,.2f}'.format(float(self.price_to_book)),
                   '{:,.2f}'.format(float(self.current_price / self.fair_price * 100))]
        except TypeError:
            row = [self.symbol, self.name, 'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a']
            logging.warning(f'[{self.symbol}] TypeError when getting table row.')
        return row
