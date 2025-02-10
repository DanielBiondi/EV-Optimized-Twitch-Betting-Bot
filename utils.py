# utils.py

import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from  webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from config import CONFIG

def create_new_chrome_driver(big=False, headless=True):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    if big:
        chrome_options.add_argument("--window-size=1920,1080")
    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Choose the service based on whether a custom chromedriver path is provided in config
    chromedriver_path = CONFIG.get("chromedriver_path", "")

    if chromedriver_path:
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def wait_and_click_all_tab(driver, timeout=20):
    try:
        # Wait for the "All" tab element to be clickable
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-tab="All"][data-test="market-tab "]'))
        )
        element.click()
    except TimeoutException:
        print(f"Timeout: 'All' tab not found within {timeout} seconds")


def sort_by_start_time(wait):
    # Click the dropdown trigger to open the options
    try:
        dropdown_trigger = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div[data-test*='dropdown-element'][data-value='RANK_RECOMMENDED']"))
        )
        dropdown_trigger.click()
        print("Clicked dropdown menu")
        # Select the "Start time" option using its data-value attribute
        start_time_option = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-value='RANK_START_TIME']"))
        )
        start_time_option.click()
        print("Changed sorting to 'Start time'")
        time.sleep(1)  # added because maybe this is the "stale" problem.
    except TimeoutException:
        print(f"Timeout: 'All' tab not found within the wait period")