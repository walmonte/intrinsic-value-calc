import my_utils
from stock import Stock
from tabulate import tabulate


if __name__ == '__main__':
    # provide stock symbol and EPS estimate for the next 5 years. Format ->'symbol': EPS next 5 years(float)
    # eps estimates can be found at finviz.com (data below is from 5/15/2022)
    symbol_dict = {'MSTR': .10, 'NFLX': .1689, 'FB': .0953, 'AMD': .2990, 'NVDA': .3075,
                   'TSLA': .3772, 'WM': .1225, 'MNST': .1395, 'ECL': .1563, 'WDAY': .1391,
                   'INTU': .1670, 'ADBE': .1425, 'ATVI': .1645, 'TTWO': .1463, 'EA': .1823,
                   'MA': .2428, 'V': .1815, 'AAPL': .1028, 'SQ': .3991, 'WMT': .0835,
                   'AMZN': .3480, 'EQT': .5271, 'FL': .3586, 'DFS': .5642, 'ZEUS': .3429,
                   'OVV': .3728, 'LL': .3000, 'EZPW': .3500, 'HT': .2780, 'BABA': .0100,
                   'JD': .2240, 'BIDU': .0544, 'ACMR': .4233, 'BGNE': .3700, 'SWK': .1311,
                   'TNC': .1500, 'LOW': .1445, 'MMM': .0717, 'PH': .1072, 'TWTR': .0750
                   }

    table = [['symbol', 'name', 'currentPrice', 'fairPrice', 'currentPricePerShare',
              'fairPricePerShare', 'P/B', 'current/fair(%)']]
    count = 0
    for key in symbol_dict:
        count += 1
        stock = Stock(key, symbol_dict[key])
        table.append(stock.get_as_row())

    my_utils.write_to_csv(table)
    print(tabulate(table, tablefmt='fancy_grid', showindex=True))
    my_utils.beep()  # beep when done
    print(f'There were {Stock.req_count} requests on this run')
