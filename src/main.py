from datetime import date

from tabulate import tabulate
from src.utils import utils
from src.stock import Stock

SYMBOLS_PATH = "C:\\projects\\intrinsic-value-calc\\data\\symbols\\symbols.txt"
RESULTS_PATH = "C:\\projects\\intrinsic-value-calc\\data\\results\\{}-results.csv"
LOGGER = utils.set_up_logger()


if __name__ == "__main__":
    symbol_list = utils.text_to_list(SYMBOLS_PATH)

    # Add headers to table
    table = [
        [
            "symbol",
            "name",
            "currentPrice",
            "fairPrice",
            "currentPricePerShare",
            "fairPricePerShare",
            "priceToBookRatio",
            "current/fair(%)",
        ]
    ]

    for symbol in symbol_list:
        stock = Stock(symbol)
        if stock.fair_price is None:
            LOGGER.info(
                "Fair price for [%s] could not be determined. Skipping...", stock.symbol
            )
        else:
            table.append(stock.get_as_row())

    utils.write_to_csv(table, RESULTS_PATH.format(date.today()))
    print(tabulate(table, tablefmt="fancy_grid", showindex=True))

    utils.beep()  # beep when done
