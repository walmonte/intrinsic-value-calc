from pytickersymbols import PyTickerSymbols
from utils import utils


PATH_TO_FILE = 'C:\\projects\\intrinsic-value-calc\\data\\symbols\\symbols.txt'
# how to use this module https://github.com/portfolioplus/pytickersymbols
stock_data = PyTickerSymbols()

sp_600_tickers = stock_data.get_sp_600_nyc_google_tickers() # returns list of strings in the format ['NYSE:LIN', 'NYSE:MMM', ...]
nasdaq_100_tickers = stock_data.get_nasdaq_100_nyc_google_tickers()
combined = sp_600_tickers + nasdaq_100_tickers

# Clean list
all_tickers = [x.split(':')[1] for x in combined]

# Write to file
utils.write_to_csv(all_tickers, PATH_TO_FILE)
