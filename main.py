from utils import utils
from stock import Stock
from tabulate import tabulate

SYMBOLS_PATH = 'data/symbols/symbols.csv'


if __name__ == '__main__':
    utils.set_up_logger()
    symbol_dict = utils.csv_to_map(SYMBOLS_PATH)

    # Add headers to table
    table = [['symbol', 'name', 'currentPrice', 'fairPrice', 'currentPricePerShare',
          'fairPricePerShare', 'priceToBookRatio', 'current/fair(%)']]
    count = 0
    for key in symbol_dict:
        count += 1
        stock = Stock(key, symbol_dict[key])
        if stock.fair_price is None:
            print(f"Fair price for {stock.symbol} is None")
            continue
        table.append(stock.get_as_row())

    utils.write_to_csv(table)
    print(tabulate(table, tablefmt='fancy_grid', showindex=True))

    utils.beep()  # beep when done