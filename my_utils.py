import csv
import logging
import os
from datetime import date
from time import sleep, ctime
from winsound import Beep

DATE_TIME_FORMAT = '%d-%b-%y %H:%M:%S'
LOG_FORMAT = '[%(asctime)s] %(process)d - %(levelname)s - %(message)s'

# Alpha Vantage API usage limits: 5 requests/minute and 500 requests/day
API_KEY = os.environ['ALPHA_VANTAGE_API_KEY']  # delete this line and uncomment the next one
# API_KEY = 'YOUR_API_KEY'   # you can get a free api key on alphavantage.co


def get_todays_date():
    return date.today()


logging.basicConfig(filename=f'logs/{get_todays_date()}.log', filemode='a', format=LOG_FORMAT, datefmt=DATE_TIME_FORMAT)


def find_wacc(beta: float):
    if beta < .08:
        return 0.05
    elif beta < 1.0:
        return 0.06
    elif beta < 1.1:
        return 0.065
    elif beta < 1.2:
        return 0.07
    elif beta < 1.3:
        return 0.075
    elif beta < 1.5:
        return 0.08
    elif beta < 1.6:
        return 0.085
    else:
        return 0.09


def build_url(func, symbol):
    base = 'https://www.alphavantage.co/query?'
    function = f'function={func.upper()}&'
    symbol_api_key = f'symbol={symbol}&apikey={API_KEY}'
    return base + function + symbol_api_key


def bad_response(resp):
    if 'Note' in resp:
        print('API REQUEST LIMIT HAS BEEN REACHED.')
        logging.error("Bad response due to going over API limits")
        return True
    return False


def beep():
    duration = 100  # milliseconds
    freq = 440  # Hz
    Beep(freq, duration)
    Beep(freq - 100, duration)
    Beep(freq, duration)
    Beep(freq, duration)
    Beep(freq - 100, duration)
    Beep(freq, duration)


def take_break():
    print(f'[{ctime()}] Wait for 1 min')
    sleep(60)


def write_to_csv(table):
    with open(f'data/results/{get_todays_date()}-results.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(table)


def parse_date(to_parse):
    return date.fromisoformat(to_parse)
