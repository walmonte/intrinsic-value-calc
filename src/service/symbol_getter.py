from pytickersymbols import PyTickerSymbols
from src.utils import utils

PATH_TO_FILE = "C:\\projects\\intrinsic-value-calc\\data\\symbols\\symbols.txt"
OTC_EXCHANGES = ["OTCMKTS", "PINK", "OTCBB", "OTCQB"]  # exchanges to exclude


def clean_ticker_list(ticker_list):
    """
    Cleans the ticker list by removing OTC exchanges and extracting the ticker symbol.
    :param ticker_list: List of tickers in the format ['NYSE:LIN', 'NYSE:MMM', ...]
    :return: Cleaned list of ticker symbols.
    """
    return list(
        map(
            lambda x: x.split(":")[1],
            filter(lambda x: x.split(":")[0].upper() not in OTC_EXCHANGES, ticker_list),
        )
    )


if __name__ == "__main__":
    # how to use this module https://github.com/portfolioplus/pytickersymbols
    stock_data = PyTickerSymbols()

    sp500 = clean_ticker_list(stock_data.get_sp_500_nyc_google_tickers())
    nasdaq100 = clean_ticker_list(stock_data.get_nasdaq_100_nyc_google_tickers())

    utils.write_list_to_text_file(sp500 + nasdaq100, PATH_TO_FILE)
