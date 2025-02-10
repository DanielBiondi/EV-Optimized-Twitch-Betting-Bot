import csv
from csv import DictReader

from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import xpath_and_css_selectors as selectors
from twitch_actions import click_prediction_button

def ensure_csv_format(file):
    """
    Ensures that the CSV file has exactly three columns ("name", "value", "domain")
    and that it uses commas as delimiters. If the file is semicolon-separated or has
    extra/missing columns, it rewrites the file in the correct format.
    """
    with open(file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
    if not lines:
        # Empty file; nothing to do.
        return

    # Determine which delimiter is used by checking the header line.
    header_line = lines[0].strip()
    delimiter = ";" if ";" in header_line else ","

    # Get header columns (stripping spaces)
    headers = [col.strip() for col in header_line.split(delimiter)]
    expected = ["name", "value", "domain"]

    # If the headers do not match the expected columns exactly, reformat the CSV.
    if headers != expected:
        reader = csv.DictReader(lines, delimiter=delimiter)
        rows = []

        # Create a mapping from expected lowercase names to the actual header names (if available)
        lower_headers = [col.lower() for col in headers]
        mapping = {}
        for col in expected:
            if col in lower_headers:
                # Get the original header name from the file.
                mapping[col] = headers[lower_headers.index(col)]
            else:
                # Column not found; will default to an empty string for every row.
                mapping[col] = None

        # Process each row, keeping only the expected keys.
        for row in reader:
            new_row = {}
            for col in expected:
                if mapping[col] is not None:
                    new_row[col] = row.get(mapping[col], "")
                else:
                    new_row[col] = ""
            rows.append(new_row)

        # Rewrite the file with a comma as delimiter and the proper header order.
        with open(file, "w", newline="", encoding="utf-8-sig") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=expected)
            writer.writeheader()
            writer.writerows(rows)

def get_cookie_values(file):
    """
    Takes all the cookies from our csv file.
    Turns them into a list of dicts
    :param file: csv file
    :return: a list of dicts
    """
    ensure_csv_format(file)
    with open(file, encoding="utf-8-sig") as f:
        dict_reader = DictReader(f)
        list_of_dicts = list(dict_reader)
    return list_of_dicts

def get_prediction_elements_with_retry(driver):
    """
    Attempts to retrieve prediction elements (blue vote, red vote, question) with retries.
    Reloads the page and increases wait time on each retry.
    Returns the elements if found, raises exception otherwise.
    """
    max_retries = 3
    timeouts = [5, 10, 20]  # Timeout in seconds for each attempt
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # Reload the page and re-click the prediction button for subsequent attempts
                driver.refresh()
                click_prediction_button(driver)

            # Wait for blue vote option with increasing timeout
            blue_vote = WebDriverWait(driver, timeouts[attempt]).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selectors.blue_vote_option_BYCSS))
            ).text
            red_vote = driver.find_element(By.CSS_SELECTOR, selectors.red_vote_option_BYCSS).text
            question = driver.find_element(By.CSS_SELECTOR, selectors.prediction_question_BYCSS).text

            return blue_vote, red_vote, question
        except (TimeoutException, NoSuchElementException) as e:
            driver.save_screenshot(f"debug/prediction_retry_attempt_{attempt + 1}.png")
            if attempt < max_retries - 1:
                print(f"Retry attempt {attempt + 1} failed. Retrying with longer timeout...")
            else:
                print("All retry attempts failed for prediction elements.")
                raise  # Re-raise the last exception after all retries
    raise Exception("All retries exhausted for prediction elements")  # Fallback exception
