import csv
import locale
import logging
from datetime import date
from time import sleep, ctime
from winsound import Beep

LOG = logging.getLogger()
### Logger utils

def set_up_logger():
    log_format = '[%(asctime)s] %(process)d - %(levelname)s - %(message)s'
    date_time_format = '%d-%b-%y %H:%M:%S'
    logging.basicConfig(filename=f'logs/{date.today()}.log', filemode='a', format=log_format, datefmt=date_time_format)
    logging.getLogger().setLevel(logging.INFO)
    return logging.getLogger()


### File utils

def csv_to_map(file_path):
    data_map = {}
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = row['ticker']
            value = float(row['eps_estimate_next_5y'])
            data_map[key] = value
    return data_map

def text_to_list(file_path):
    try:
        with open(file_path, 'r') as file:
            data_list = [line.rstrip('\n') for line in file]
            return data_list
    except FileNotFoundError:
        msg = f"Error: File not found at {file_path}"
        print(msg)
        LOG.info(msg)
        return None
    except Exception as e:
        msg = f"An error occurred while reading the file: {e}"
        print(msg)
        LOG.info(msg)
        return None

def write_list_to_text_file(data_list, file_path):
    try:
        with open(file_path, 'w') as file:
            for item in data_list:
                file.write(str(item) + '\n')
        msg = f"List successfully written to {file_path}"
        print(msg)
        LOG.info(msg)
    except Exception as e:
        msg = f"An error occurred while writing to CSV: {e}"
        print(msg)
        LOG.info(msg)

def write_to_csv(table, file_path):
    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(table)
        msg = f"List successfully written to {file_path}"
        print(msg)
        LOG.info(msg)
    except Exception as e:
        msg = f"An error occurred while writing to CSV: {e}"
        print(msg)
        LOG.info(msg)


### Calc utils

# Weighted Average Cost of Capital (WACC) calculation
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

def calculate_compound_annual_growth_rate(start_value: float, end_value: float, periods: int):
    if start_value <= 0 or periods <= 0:
        return 0.0
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
    print(f'[{ctime()}] Wait for 1 min')
    sleep(60)

def parse_date(to_parse):
    return date.fromisoformat(to_parse)
