import csv
import locale
import logging
from datetime import date
from fileinput import filename
from time import sleep, ctime
from winsound import Beep

LOGGER = logging.getLogger(__name__)
### Logger utils

def set_up_logger():

    log_format = '{asctime}: [{levelname}] - At [{name}]: {message}'
    date_time_format = '%d-%b-%y %H:%M:%S'

    # create a handler for console output (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, style='{', datefmt=date_time_format)
    console_handler.setFormatter(console_formatter)

    # create a handler for file output (DEBUG and above)
    file_handler = logging.FileHandler(f'logs/{date.today()}.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format, style='{', datefmt=date_time_format)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(format=log_format,  datefmt=date_time_format, style='{', level=logging.INFO, handlers=[console_handler, file_handler])

    return logging.getLogger()


### File utils

def csv_to_map(file_path):
    data_map = {}
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = row['ticker']
            value = float(row['eps_estimate_next_5y'])
            data_map[key] = value
    return data_map

def text_to_list(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data_list = [line.rstrip('\n') for line in file]
            return data_list
    except FileNotFoundError:
        LOGGER.info("Error: File not found at %s", file_path)
        return None
    except Exception as e:
        LOGGER.info("An error occurred while reading the file: %s", e)
        return None

def write_list_to_text_file(data_list, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            for item in data_list:
                file.write(str(item) + '\n')
        LOGGER.info("List successfully written to %s", file_path)
    except Exception as e:
        LOGGER.info("An error occurred while writing to CSV: %s", e)

def write_to_csv(table, file_path):
    if len(table) <= 1: # if table has only header row, do not write to file
        LOGGER.info("Results table is empty or has only header row. No data written to results file.")
        return

    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(table)
        LOGGER.info("[%d] rows successfully written to results file: %s", len(table) - 1, file_path)
    except Exception as e:
        LOGGER.info("An error occurred while writing to CSV: %s",e)


### Calc utils

def find_wacc(beta: float):
    """
    Calculate Weighted Average Cost of Capital (WACC) based on the beta value.
    :param beta:
    :return:
    """
    wacc = 0.09

    if beta < .08:
        wacc = 0.05
    elif beta < 1.0:
        wacc = 0.06
    elif beta < 1.1:
        wacc = 0.065
    elif beta < 1.2:
        wacc = 0.07
    elif beta < 1.3:
        wacc = 0.075
    elif beta < 1.5:
        wacc = 0.08
    elif beta < 1.6:
        wacc = 0.085

    return wacc

def calculate_annual_growth_rate(end_value: float, start_value: float, periods: int):
    """
    Calculate the Annual Growth Rate (AGR) between two values over a number of periods.
    :param end_value: latest value in a series. In this case, the EPS for the last year available.
    :param start_value: oldest value in a series. In this case, the EPS for the first year available.
    :param periods: number of periods between start and end value. In this case, the number of years.
    :return: Annual growth rate as a decimal. For example, 0.05 for 5%.
    """
    if periods <= 0:
        return None
    elif end_value <= 0: # if current EPS is negative or zero, discard the calculation
        return None
    elif start_value <= 0: # use linear growth rate formula for 'turnaround cases' (where EPS goes from loss to profit)
        return (end_value - start_value) / periods / abs(start_value)

    # if start and end EPS are positive, use standard compound annual growth rate (CAGR) formula
    return ((end_value / start_value) ** (1 / periods)) - 1


def safe_float(i):
    if i == 'None':
        return 0.0
    return float(i)

def format_currency(amount, local_str=''):
    try:
        if local_str:
            locale.setlocale(locale.LC_ALL, local_str)
        else:
            locale.setlocale(locale.LC_ALL, '')  # Use default locale

        if abs(amount) >= 1_000_000_000:
            formatted_amount = locale.currency(amount / 1_000_000_000, grouping=True) + " B"
        elif abs(amount) >= 1_000_000:
            formatted_amount = locale.currency(amount / 1_000_000, grouping=True) + " M"
        else:
            formatted_amount = locale.currency(amount, grouping=True)

        return formatted_amount

    except locale.Error:
        return "N/A"
    finally:
        locale.setlocale(locale.LC_ALL, '') # Reset locale to default


### Misc utils

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
    LOGGER.info('[%s] Wait for 1 min', ctime())
    sleep(60)

def parse_date(to_parse):
    return date.fromisoformat(to_parse)
