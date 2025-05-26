import csv
import locale
import logging
from datetime import date
from time import sleep, ctime
from winsound import Beep

LOGGER = logging.getLogger(__name__)
### Logger utils


def set_up_logger():
    """Sets up logger with a specific format and handlers for console and file output."""
    log_format = "{asctime}: [{levelname}] - At [{name}]: {message}"
    date_time_format = "%d-%b-%y %H:%M:%S"

    # create a handler for console output (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        log_format, style="{", datefmt=date_time_format
    )
    console_handler.setFormatter(console_formatter)

    # create a handler for file output (DEBUG and above)
    file_handler = logging.FileHandler(
        f"logs/{date.today()}.log", mode="a", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format, style="{", datefmt=date_time_format)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(
        format=log_format,
        datefmt=date_time_format,
        style="{",
        level=logging.INFO,
        handlers=[console_handler, file_handler],
    )

    return logging.getLogger()


### File utils


def csv_to_map(file_path):
    """Reads a CSV file and converts it to a dictionary
    mapping ticker symbols to their EPS estimates for the next 5 years."""
    data_map = {}
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = row["ticker"]
                value = float(row["eps_estimate_next_5y"])
                data_map[key] = value
    except FileNotFoundError:
        LOGGER.info("Error: File not found at %s", file_path)
    except KeyError as e:
        LOGGER.error(
            "Error: Missing expected column in CSV file: %s. Please check the file format.",
            e,
        )
    except IOError:
        LOGGER.error(
            "Error: An input/output error occurred while reading from %s.", file_path
        )
    except EOFError:
        LOGGER.error(
            "Error: Reached the end of the file unexpectedly while reading from %s.",
            file_path,
        )
    return data_map


def text_to_list(file_path):
    """Reads a text file and returns a list of strings, each representing a line in the file."""
    data = None
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data_list = [line.rstrip("\n") for line in file]
            data = data_list
    except FileNotFoundError:
        LOGGER.info("Error: File not found at %s", file_path)
    except IOError:
        LOGGER.error(
            "Error: An input/output error occurred while reading from %s.", file_path
        )
    except EOFError:
        LOGGER.error(
            "Error: Reached the end of the file unexpectedly while reading from %s.",
            file_path,
        )

    return data


def write_list_to_text_file(data_list, file_path):
    """Writes a list of strings to a text file, each item on a new line."""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            for item in data_list:
                file.write(str(item) + "\n")
        LOGGER.info("List successfully written to %s", file_path)
    except IOError:
        LOGGER.error(
            "Error: An input/output error occurred while writing to %s.", file_path
        )


def write_to_csv(table, file_path):
    """Writes a list of lists (table) to a CSV file.
    :param table: List of lists, where each inner list represents a row in the CSV.
    :param file_path: Path to the CSV file where the data should be written."""

    if len(table) <= 1:  # if table has only header row, do not write to file
        LOGGER.info(
            "Results table is empty or has only header row. No data written to results file."
        )
        return

    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(table)
        LOGGER.info(
            "[%d] rows successfully written to results file: %s",
            len(table) - 1,
            file_path,
        )
    except IOError:
        LOGGER.error(
            "Error: An input/output error occurred while writing to %s.", file_path
        )


### Calc utils


def find_wacc(beta: float):
    """Calculate Weighted Average Cost of Capital (WACC) based on the beta value.
    :param beta:
    :return:
    """
    wacc = 0.09

    if beta < 0.08:
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
    """Calculate the Annual Growth Rate (AGR) between two values over a number of periods.
    :param end_value: latest value in a series.
    :param start_value: oldest value in a series.
    :param periods: number of periods between start and end value.
    :return: Annual growth rate as a decimal. For example, 0.05 for 5%.
    """
    if (
        periods <= 0 or end_value <= 0
    ):  # if current EPS is negative or zero, discard the calculation
        return None

    if (
        start_value <= 0
    ):  # use linear growth rate formula for 'turnaround cases' (where EPS goes from loss to profit)
        return (end_value - start_value) / periods / abs(start_value)

    # if start and end EPS are positive, use standard compound annual growth rate (CAGR) formula
    return ((end_value / start_value) ** (1 / periods)) - 1


def safe_float(i):
    """Converts a string to a float, handling 'None' and empty strings gracefully."""
    if i == "None":
        return 0.0
    return float(i)


def format_currency(amount, locale_str=""):
    """Formats a given amount as currency, adding appropriate suffixes for millions and billions.
    :param amount: float, the amount to format as currency.
    :param locale_str: optional locale string, e.g. 'en_US.UTF-8' for US English.
    :return:
    """
    try:
        locale.setlocale(locale.LC_ALL, locale_str)

        if abs(amount) >= 1_000_000_000:
            formatted_amount = (
                locale.currency(amount / 1_000_000_000, grouping=True) + " B"
            )
        elif abs(amount) >= 1_000_000:
            formatted_amount = locale.currency(amount / 1_000_000, grouping=True) + " M"
        else:
            formatted_amount = locale.currency(amount, grouping=True)

        return formatted_amount

    except locale.Error:
        return "N/A"
    finally:
        locale.setlocale(locale.LC_ALL, "")  # Reset locale to default


### Misc utils


def beep():
    """Plays a series of beeps to indicate that the app is done running."""
    duration = 100  # milliseconds
    freq = 440  # Hz
    Beep(freq, duration)
    Beep(freq - 100, duration)
    Beep(freq, duration)
    Beep(freq, duration)
    Beep(freq - 100, duration)
    Beep(freq, duration)


def take_break():
    """Pauses the execution for 1 minute to avoid hitting API rate limits."""
    LOGGER.info("[%s] Wait for 1 min", ctime())
    sleep(60)


def parse_date(to_parse):
    """Parses a date string in the format 'YYYY-MM-DD' and returns a date object.
    :param to_parse: Date string in 'YYYY-MM-DD' format.
    :return: A date object representing the parsed date.
    """
    return date.fromisoformat(to_parse)
