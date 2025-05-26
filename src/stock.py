import csv
import logging
import os
import traceback
from datetime import date

from src.utils import utils
from src.service.data_service import DataService

BASE_DIR = "C:\\projects\\intrinsic-value-calc"
CACHE_FILE = f"{BASE_DIR}\\data\\cache.csv"
LAST_CACHE_DT_FILE = f"{BASE_DIR}\\data\\date_of_last_cache.txt"
CACHE_USEFUL_LIFE = 30  # days
LOGGER = logging.getLogger(__name__)


class Stock:
    """
    A class representing a stock and its financial data.
    """

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
        """
        Fetches data for the stock from the API or from a CSV file.
        :param data_service: A DataService object to fetch data from the API.
        :return: void
        """
        if not self.get_data_from_csv():
            try:
                response = data_service.fetch_all_data(self.symbol)
                if response is None:
                    LOGGER.warning("[%s] Failed to fetch data from API.", self.symbol)
                    return

                cash_flow = response["cash_flow"]
                balance_sheet = response["balance_sheet"]
                overview = response["overview"]
                global_quote = response["global_quote"]
                earnings = response["earnings"]

                op_cashflow = utils.safe_float(cash_flow["operatingCashflow"])
                capex = utils.safe_float(cash_flow["capitalExpenditures"])
                self.free_cash_flow = op_cashflow - capex

                self.cash = utils.safe_float(
                    balance_sheet["cashAndShortTermInvestments"]
                )
                self.total_debt = utils.safe_float(
                    balance_sheet["shortLongTermDebtTotal"]
                )

                self.name = overview["Name"]
                self.price_to_book = utils.safe_float(overview["PriceToBookRatio"])
                self.beta = utils.safe_float(overview["Beta"])
                self.outstanding_shares = utils.safe_float(
                    overview["SharesOutstanding"]
                )

                self.current_price = utils.safe_float(global_quote["05. price"])
                self.calculate_eps_next_5y(earnings)
            except ValueError:
                LOGGER.error(
                    "ValueError: Could not convert data to float for [%s]. %s",
                    self.symbol,
                    traceback.format_exc(),
                )
                return
            except KeyError:
                LOGGER.error(
                    "KeyError: missing key data point for [%s]. Cancelling... %s",
                    self.symbol,
                    traceback.format_exc(),
                )
                return

            self.compute_valuation()

    def calculate_eps_next_5y(self, earnings):
        """
        Calculates the expected EPS growth for the next 5 years using data from
        the previous `len(earnings)` years.
        :param earnings: The earnings data fetched from the API.
        :return: void
        """
        periods = len(earnings)
        if periods < 1 or earnings[0]["reportedEPS"] is None:
            self.eps_next_5y = 0.0
        else:
            latest_eps = utils.safe_float(earnings[0]["reportedEPS"])
            oldest_eps = utils.safe_float(earnings[-1]["reportedEPS"])
            eps_agr = utils.calculate_annual_growth_rate(
                latest_eps, oldest_eps, periods
            )

            if eps_agr is None:
                self.eps_next_5y = None
                LOGGER.info(
                    "[%s] Calculated EPS AGR over the last %d periods: %s",
                    self.symbol,
                    periods,
                    eps_agr,
                )
            else:
                self.eps_next_5y = (
                    eps_agr / 2
                )  # using half of AGR to get a conservative EPS estimate for the next 5 years
                LOGGER.info(
                    "[%s] Calculated EPS AGR over the last %d periods: %.2f",
                    self.symbol,
                    periods,
                    eps_agr * 100,
                )

    def compute_valuation(self):
        """
        Computes the valuation of the stock using the Discounted Cash Flow (DCF) method.
        :return: void
        """
        discounted_cashflow = 0
        if self.eps_next_5y is not None:
            eps_6_to_10y = self.eps_next_5y / 2
            eps_10to_20y = eps_6_to_10y / 2
            wacc = float(utils.find_wacc(self.beta))

            discount_factor = 1 / (1 + wacc)
            free_cashflow_today = self.free_cash_flow

            for i in range(1, 6):
                discounted_cashflow += (
                    free_cashflow_today
                    * (1 + self.eps_next_5y) ** i
                    * discount_factor**i
                )

            free_cashflow_year_5 = free_cashflow_today * (1 + self.eps_next_5y) ** 5
            for i in range(1, 6):
                discounted_cashflow += (
                    free_cashflow_year_5
                    * (1 + eps_6_to_10y) ** i
                    * discount_factor ** (i + 5)
                )

            free_cashflow_year_10 = free_cashflow_year_5 * (1 + eps_6_to_10y) ** 5
            for i in range(1, 11):
                discounted_cashflow += (
                    free_cashflow_year_10
                    * (1 + eps_10to_20y) ** i
                    * discount_factor ** (i + 10)
                )

            self.present_value = self.cash - self.total_debt + discounted_cashflow
            self.fair_price = self.present_value / self.outstanding_shares

            self.save_data_to_csv()

    def get_data_from_csv(self):
        """
        Retrieves data from the cache CSV file. If the cache is older than 30 days,
        doesn't exist, or is empty, it creates a new cache file with headers only.
        :return: True if data was found in the cache, False otherwise.
        """
        with open(LAST_CACHE_DT_FILE, mode="r", newline="", encoding="utf-8") as f:
            latest_cache = f.read()
            latest_cache = utils.parse_date(latest_cache)

        cache_is_too_old = (date.today() - latest_cache).days > CACHE_USEFUL_LIFE
        if (
            cache_is_too_old
            or (not os.path.isfile(CACHE_FILE))
            or (os.path.getsize(CACHE_FILE) == 0)
        ):
            with open(CACHE_FILE, mode="w", newline="", encoding="utf-8") as f:
                headers = [
                    "symbol",
                    "name",
                    "fcc",
                    "cash",
                    "total_debt",
                    "shares",
                    "beta",
                    "eps_next_5y",
                    "current_price",
                    "fair_price",
                    "price_to_book",
                    "PV",
                ]
                writer = csv.writer(f)
                writer.writerow(headers)
            LOGGER.info(
                "Cache file was over 30 days old, didn't exist or was empty."
                " It was set to have headers only."
            )
            return False

        with open(CACHE_FILE, mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if row["symbol"].upper() == self.symbol:
                    self.name = row["name"]
                    self.free_cash_flow = float(row["fcc"])
                    self.cash = float(row["cash"])
                    self.total_debt = float(row["total_debt"])
                    self.outstanding_shares = float(row["shares"])
                    self.beta = float(row["beta"])
                    self.current_price = float(row["current_price"])
                    self.fair_price = float(row["fair_price"])
                    self.price_to_book = float(row["price_to_book"])
                    self.present_value = float(row["PV"])

                    LOGGER.info("Retrieved [%s] from cache.csv.", self.symbol)
                    return True

        return False

    def save_data_to_csv(self):
        """
        Saves the stock data to the cache CSV file.
        :return: void
        """
        fields = [
            self.symbol,
            self.name,
            self.free_cash_flow,
            self.cash,
            self.total_debt,
            self.outstanding_shares,
            self.beta,
            self.eps_next_5y,
            self.current_price,
            self.fair_price,
            self.price_to_book,
            self.present_value,
        ]

        with open(CACHE_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)

        with open(LAST_CACHE_DT_FILE, mode="w", newline="", encoding="utf-8") as f:
            f.write(str(date.today()))
            LOGGER.info("Updated date of last cache.")

    def get_as_row(self):
        """
        Returns a list representing the stock data in a row format for display.
        :return: An instance of Stock as a list.
        """
        try:
            row = [
                self.symbol,
                self.name,
                utils.format_currency(
                    float(self.current_price * self.outstanding_shares)
                ),
                utils.format_currency(float(self.present_value)),
                utils.format_currency(float(self.current_price)),
                utils.format_currency(float(self.fair_price)),
                f"{float(self.price_to_book):,.2f}",
                "{float(self.current_price / self.fair_price * 100):,.0f}%",
            ]
        except TypeError as err:
            row = [self.symbol, self.name, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]
            LOGGER.warning(
                "[%s] TypeError when getting table row. Err: %s", self.symbol, err
            )
        return row
