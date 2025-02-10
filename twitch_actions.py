# twitch_actions.py
import traceback

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import time

from point_logic import get_points, calculate_bet
from prediction_logging import prediction_history
import xpath_and_css_selectors as selectors

# TODO: i think i need the predictions lock for this. just pass it through to this function
#  we only access it probably atomically 4 times total but still?
def place_bet_on_channel(channel, prediction_info, driver):
    """
    it tells point_logic to calculate the bet and makes the bet.
    After attempting to make the bet,
    it verifies that the bet was actually made by checking that the bet amount
    appears with "spent" in the HTML. If verification fails, it retries the bet
    up to MAX_RETRIES times.
    Returns: bool indicating if the bet was successfully placed.
    """
    if prediction_info.get("bet_placed", False):  # means: if bet_placed is true
        print(f"Bet already placed for {channel}")
        return False

    max_retries = 3
    for retry in range(max_retries + 1):
        try:
            # Retrieve the current points and vote counts
            points_text_element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, selectors.points_text_xpath))
            )
            my_points = get_points(points_text_element.text)    # TODO: uncomment this line and comment the hard coded million out

            blue_votes_element = driver.find_element(By.XPATH, selectors.blue_votes)
            red_votes_element = driver.find_element(By.XPATH, selectors.red_votes)
            blue_votes_count = get_points(blue_votes_element.text)
            red_votes_count = get_points(red_votes_element.text)

            # Calculate optimal bet amount and color
            bet_amount, bet_color = calculate_bet(
                my_points,
                blue_votes_count,
                red_votes_count,
                prediction_info['team1_odds'],
                prediction_info['team2_odds']
            )

            place_the_bet(bet_amount, bet_color, driver)

            # Verify that the bet was actually made (i.e., the bet_amount is "spent")
            if verify_bet(bet_amount, driver):
                prediction_history(channel, bet_amount, bet_color, 1, my_points, bet_amount)
                print(f"{channel} placed bet!!!")
                return True
            else:
                print(f"{channel}: Bet verification failed for {bet_amount} points.")
                # Save debugging information with 'retry' in the filename.
                driver.save_screenshot(f"debug/retry{bet_amount}_{retry}.png")
                with open(f"debug/retry{bet_amount}_{retry}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                if retry < max_retries:
                    print(f"Retrying bet for {channel} (retry {retry+1}/{max_retries})...")
                    # Optionally, add a short wait before retrying if needed.
                    continue
                else:
                    print(f"Max retries reached for {channel}. Bet not placed.")
                    return False

        except Exception as e:
            print(channel, f"Error placing bet: {e}")
            traceback.print_exc()
            driver.save_screenshot(f"debug/_uhmmm{channel, retry}.png")
            with open(f"debug/_uhmmm.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return False
    return False


def verify_bet(bet_amount, driver):
    # XPath to find a <p> element that contains both the bet amount and the word "spent"
    xpath_expression = f"//p[contains(., '{bet_amount}') and contains(., 'spent')]"
    try:
        WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, xpath_expression))
        )
        return True
    except TimeoutException:
        return False


def click_get_started(driver):
    """apparently, sometimes this is needed."""
    try:
        get_started_button = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.XPATH, selectors.get_started_button))
        )
        get_started_button.click()
        print("Clicked 'Get Started!' button")
    except TimeoutException:
        print("No 'Get Started!' button found, continuing...")


def get_timer_text(driver):
    # Try data-test-selector first
    try:
        timer_element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-selector='predictions-list-item__subtitle']"))
        )
        return timer_element.text
    except TimeoutException:
        print("timeout in get timer text, think about swapping try and except if this prints regularly")
        # If data-test-selector fails, try xpath
        try:
            timer_xpath = selectors.prediction_timer_xpath
            timer_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, timer_xpath))
            )
            return timer_element.text
        except TimeoutException:
            return None

def place_the_bet(bet_amount, bet_color, driver):
    print(f"Placing bet: {bet_amount} on {bet_color}")
    try:
        try:  # Find all input fields
            input_fields = WebDriverWait(driver, 2).until(
                EC.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR, "input[data-a-target='tw-input']")
                )
            )
        except TimeoutException:
            print("New selector failed; trying the old selector...")
            input_fields = WebDriverWait(driver, 2).until(
                EC.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR, "input[data-test-selector='prediction-checkout-input']")
                )
            )
        if bet_color == "blue":
            # The blue input is the first one
            bet_field = input_fields[0]
            bet_button = driver.find_element(By.CSS_SELECTOR,
                                         "button div[style*='background-color: rgb(56, 122, 255)']")
        else:
            # The pink input is the second one
            bet_field = input_fields[1]
            bet_button = driver.find_element(By.CSS_SELECTOR,
                                         "button div[style*='background-color: rgb(245, 0, 155)']")
        bet_field.send_keys(str(bet_amount))
        bet_button.click()
    except Exception as e:
        print(f"Error placing bet: {str(e)}")
        driver.save_screenshot(f"debug/{bet_amount}.png")        # Save a screenshot for visual debugging
        html_source = driver.page_source
        with open(f"debug/{bet_amount}.html", "w", encoding="utf-8") as f:
            f.write(html_source)
        traceback.print_exc()

    #if bet_color == "blue":
    #    bet_field = WebDriverWait(driver, 10).until(
    #        By.XPATH,"(//input[@data-a-target='tw-input'])[1]"
    #    )
    #    bet_button = driver.find_element(By.XPATH, selectors.blue_button)
    #else:
    #    bet_field = WebDriverWait(driver, 10).until(
    #        By.XPATH, "(//input[@data-a-target='tw-input'])[2]"
    #    )
    #    bet_button = driver.find_element(By.XPATH, selectors.red_button)



def click_points_element(driver):
    max_attempts = 3
    attempt = 0

    initial_button_xpath = selectors.channel_points_button
    alt_button_css = "button[aria-label='Bits and Points Balances']"

    while attempt < max_attempts:
        try:
            # Try to find either button

            try:
                points_button = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, initial_button_xpath))
                )
            except TimeoutException:
                print("timeout at click points element. think about swapping try and except if this prints regularly")
                points_button = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, alt_button_css))
                )
            # note: i got rid of a bit here because the problem was somewhere else a while ago.
            #  this should be robust like it is.
            # Scroll element into view
            #driver.execute_script("arguments[0].scrollIntoView(true);", points_button)
            #WebDriverWait(driver, 1).until(EC.visibility_of(points_button))
            points_button.click()
            #time.sleep(1)
            print("Clicked channel points button")
            # Verify the points menu opened by checking for the header element
            try:
                WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.ID, "channel-points-reward-center-header"))
                )
                print("Points menu opened successfully")
                return  # Exit function if successful
            except TimeoutException:
                print(f"Points menu didn't open on attempt {attempt + 1}, retrying...")
                attempt += 1
                continue

        except TimeoutException:
            print("No points element button found, continuing...")

def click_prediction_button(driver):
    try:
        prediction_button = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-selector='predictions-list-item__title']"))
        )
        prediction_button.click()
        print("Clicked channel prediction button")
    except Exception as e:
        print(f"Error: {e}")
        print("No prediction element found")


def click_predict_custom_amount(driver):
    """
    Clicks the 'Predict with Custom Amount' button in the prediction interface.
    """
    try:
        # Use the unique data-test-selector attribute to locate the button
        custom_amount_selector = "button[data-test-selector='prediction-checkout-active-footer__input-type-toggle']"

        custom_amount_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, custom_amount_selector))
        )
        custom_amount_button.click()
        print("Successfully clicked 'Predict with Custom Amount' button")

    except TimeoutException:
        print("Timeout: Custom amount button not found within 10 seconds")
    except Exception as e:
        print(f"Error clicking custom amount button: {str(e)}")
        traceback.print_exc()