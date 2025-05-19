from datetime import date

from utils import utils
from stock import Stock
from tabulate import tabulate

SYMBOLS_PATH = 'C:\\projects\\intrinsic-value-calc\\data\\symbols\\symbols.txt'
RESULTS_PATH = 'C:\\projects\\intrinsic-value-calc\\data\\results\\{}-results.csv'

if __name__ == '__main__':
    utils.set_up_logger()
    symbol_list = utils.text_to_list(SYMBOLS_PATH)

    # Add headers to table
    table = [['symbol', 'name', 'currentPrice', 'fairPrice', 'currentPricePerShare',
          'fairPricePerShare', 'priceToBookRatio', 'current/fair(%)']]
    count = 0
    for symbol in symbol_list:
        count += 1
        stock = Stock(symbol)
        if stock.fair_price is None:
            print(f"Fair price for {stock.symbol} is None")
            continue
        table.append(stock.get_as_row())

    utils.write_to_csv(table, RESULTS_PATH.format(date.today()))
    print(tabulate(table, tablefmt='fancy_grid', showindex=True))

    utils.beep()  # beep when done