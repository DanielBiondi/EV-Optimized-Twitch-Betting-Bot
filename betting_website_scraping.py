# betting_website_scraping.py

import time
import traceback
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from use_openai import get_twitch_team_selectors
from utils import create_new_chrome_driver, sort_by_start_time
from config import CONFIG


def scrape_with_retry():
    """retry wrapper for scrape_betting_site_lol_matches, because it seems to fail randomly."""
    max_retries = 20
    delays = [1, 2, 4, 8, 16] + [30] * 15  # 20 elements total

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} of {max_retries}")
            data = scrape_betting_site_lol_matches()

            # Check if data is valid (non-empty and contains URLs)
            if data and any(match.get('url') for match in data):
                print("Scraping successful.")
                return data
            else:
                print("Scraped data is empty or invalid. Retrying...")
        except Exception as e:
            print(f"Scraping attempt {attempt + 1} failed with error: {str(e)}")

        # Determine wait time
        wait_time = delays[attempt] if attempt < len(delays) else 30
        print(f"Waiting {wait_time} seconds before next attempt...")
        time.sleep(wait_time)

    raise Exception("Failed to scrape valid data after 20 retries")

def scrape_betting_site_lol_matches():  # TODO: should probably be called periodically too, just idk like every 5 mins or so?
    #betting_url = "https://gg258.bet/en?sportId=esports_dota_2"
    betting_url = CONFIG.get("betting_website_url", "https://gg258.bet/en?sportId=esports_league_of_legends")

    driver = create_new_chrome_driver(big=True)#webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(betting_url)
        print("loaded league base url")

        wait = WebDriverWait(driver, 15, 0.2)  # used in wait.until

        sort_by_start_time(wait)

        betlines = wait.until( # Wait for betlines to load
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.relative.flex.flex-col.bg-surface-middle"))
        )

        matches = []
        for betline in betlines:
            # Extract URL from data-label
            try:
                link_element = betline.find_element(
                    By.XPATH, './/*[@data-action="Click on title"]/ancestor::a'
                )
                url = link_element.get_attribute('href')
            except Exception as e:
                print("exception get url xd: ", e)
                url = None

            try:
                # Get team names
                teams = [elem.text for elem in betline.find_elements(
                    By.CSS_SELECTOR, '[data-test="competitor-title"]'
                )]
            except Exception as e:
                teams = None
                print("exception # Get team names: ", e)

            # Get moneyline odds
            try:
                moneyline_section = betline.find_element(
                    By.CSS_SELECTOR, '[data-test="top-markets"] > div:first-child'
                )
                odds = [elem.text for elem in moneyline_section.find_elements(
                    By.CSS_SELECTOR, '[data-test="odd-button__result"]'
                )]
            except  Exception as e:
                odds = ["-", "-"]
                print("exception # Get odds: ", e)
            try:
                # Extract date/time/map info
                date_element = betline.find_element(
                    By.CSS_SELECTOR, 'div.text-sm.text-grey-500'
                )
                date_parts = [elem.text for elem in date_element.find_elements(By.XPATH, './*')]
                date_str = " - ".join(date_parts) if len(date_parts) > 1 else date_parts[0]
            except Exception as e:
                date_str = "__"
                print("exception # Get date: ", e)
            # Construct match dictionary
            match_data = {
                "tournament": "",
                "url": url,
                "team1_name": teams[0] if len(teams) > 0 else "",
                "team1_odds": odds[0] if len(odds) > 0 else "-",
                "team2_name": teams[1] if len(teams) > 1 else "",
                "team2_odds": odds[1] if len(odds) > 1 else "-",
                "date": date_str
            }
            print("match data: ", match_data)

            matches.append(match_data)
        print(matches)
        return matches

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return []


#  that means that the first time it get called it needs to be differnt. or a differnt function gets called the first time.
#  i think two differnt funcions. update/get match details
#  todo: i think we should save the odds website containers which we can .text to get the odds in the prediction with
#   the driver, if its not there then we just dont update it, maybe it comes again and its just paused.
def get_updated_match_odds(driver, market_name, team1_title, team2_title):
    team1_odds = None
    team2_odds = None

    try:
        # Get team 1 odds if selector is provided
        if market_name and team1_title:
            team1_odds = get_odds(driver, market_name, team1_title)
        # Get team 2 odds if selector is provided
        if market_name and team2_title:
            team2_odds = get_odds(driver, market_name, team2_title)

    except TimeoutException:
        print(f"Timeout waiting for odds elements - selectors may be invalid or page structure changed")
    except NoSuchElementException as e:
        print(f"Odds element not found: {str(e)}")
    except Exception as e:
        print(f"Unexpected error retrieving odds: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
    # dont return error messages lmao that happened before somehow lets return None instead
    print("XXXXteam1_odds, team2_odds returning them here haha", team1_title,": ",team1_odds, team2_title, team2_odds)

    if not isinstance(team1_odds, (int, float)) or not isinstance(team2_odds, (int, float)):
        return None, None
    print("team1_odds, team2_odds returning them here haha", team1_title,": ",team1_odds, team2_title, team2_odds)
    return team1_odds, team2_odds



def get_team_odds_selectors(driver, twitch_team1_name, twitch_team2_name, prediction_question):
    """the odds selectors are the right odds selectors for twitch team1 and twitch team 2 from the betting site."""
    market_name_and_titles = scrape_odds_selectors(driver)
    market_name, team1_title, team2_title = get_twitch_team_selectors(market_name_and_titles,
                                                                         twitch_team1_name,
                                                                         twitch_team2_name,
                                                                         prediction_question)
    print("selectors:", market_name, team1_title, team2_title)
    return market_name, team1_title, team2_title

# TODO: profiler says this takes some time even without retry. 17 seconds for 3 times called. my only idea to optimize
#  would be to choose less market_containers. actually not sure. probably won't optimize, only needs to be done once per
#  prediction and it's only 5 seconds
def scrape_odds_selectors(driver):
    """
    Scrape and structure betting containers from match page
    Using Retry Mechanism that reloads the page because the page can fail to load.
    """

    retry_delays = [0, 1, 10, 20, 60, 120, 240]  # Initial attempt + 6 retries

    for attempt, delay in enumerate(retry_delays):
        if attempt > 0:  # Skip delay and refresh for the first attempt
            print(f"Retry attempt {attempt}. Waiting {delay} seconds...")
            time.sleep(delay)   #
            print("Refreshing the page...")
            driver.refresh()    # sometimes the page does not load and needs to be reloaded

        try:
            market_names_and_titles = []
            # Locate all market containers (adjust selector if needed, but works with provided HTML)
            wait = WebDriverWait(driver, 10)  # 10 seconds timeout
            market_containers = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.mb-2.w-full.bg-surface-middle'))
            )
            for container in market_containers:
                # Extract market name (e.g. "Map 3 - Winner")
                market_name_element = container.find_element(By.CSS_SELECTOR, '[data-test="market-name"]')
                market_name = market_name_element.text.strip()

                # Find market group containing the individual bet buttons
                market_group = container.find_element(By.CSS_SELECTOR, '[data-test="market-group"]')

                # Get all bet buttons in this market (uses starts-with selector to capture variations)
                bet_buttons = market_group.find_elements(By.CSS_SELECTOR, '[data-test^="odd-button"]')

                for button in bet_buttons:
                    try:
                        # Extract team/bet title and odds
                        title_element = button.find_element(By.CSS_SELECTOR, '[data-test="odd-button__title"]')
                        title = title_element.text.strip()
                    except Exception as e:
                        #  print(f"Skipping malformed bet button: {e}") This was printed so often so annoying
                        continue

                    # Store element reference along with parsed data
                    market_names_and_titles.append({
                        "market_name": market_name,
                        "title": title
                    })
            #print("market_names_and_titles", market_names_and_titles)
            return market_names_and_titles

        except Exception as e:
            print(f"Error scraping containers: {e}")
            driver.save_screenshot(f"debug/Error scraping containers.png")
            traceback.print_exc()
    return []

# if LM doesnt return it exactly like we expect it, it works anyways at least if the lm didnt completely butcher it.
def get_odds(driver, market, title):
    title_clean = title.strip().lower()
    market_clean = market.strip().lower()
    xpath = f"""
    //div[@data-test='market-name' and translate(
              normalize-space(),
              'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
              'abcdefghijklmnopqrstuvwxyz'
          ) = '{market_clean}']
    /ancestor::div[contains(@class, 'mb-2')]
    /div[@data-test='market-group']
    //div[@data-test='odd-button__title' and translate(
              normalize-space(), 
              'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 
              'abcdefghijklmnopqrstuvwxyz'
          ) = '{title_clean}'] 
    /ancestor::div[contains(@class, 'flex-col')]
    /div[contains(@class, 'relative')][2]
    /div[@data-test='odd-button__result']
    """
    try:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        odds_text = element.text
        if odds_text == "-":  # dont throw valuerror here, this or floats are expected.
            print(f"Odds not available for {title} in {market}.")
            return None
        team_odds = float(odds_text)
        return team_odds
    except ValueError:
        traceback.print_exc()
        return None
    except Exception as e:
        driver.save_screenshot(f"debug/{market} {title}.png")
        traceback.print_exc()
        return None
