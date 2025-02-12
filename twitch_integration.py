# twitch_integration.py
import time
from threading import Timer, Lock
import traceback
from utils import create_new_chrome_driver, wait_and_click_all_tab
from concurrent.futures import ThreadPoolExecutor, as_completed

from twitch_utils import get_cookie_values, get_prediction_elements_with_retry
from betting_website_scraping import get_updated_match_odds, get_team_odds_selectors
from twitch_actions import click_get_started, click_points_element, click_prediction_button, \
    place_bet_on_channel, get_timer_text, click_predict_custom_amount
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from use_openai import get_url_from_openai


#active_twitch_predictions = {

#    }
#}

# Betting site data
#self.active_betting_site_data = {
#    "https://...": {

#    }
#}


class TwitchIntegration:
    def __init__(self):

        self.active_twitch_predictions = {}
        self.active_betting_site_data = {}
        self.cookies = get_cookie_values("twitch_cookies.csv")

        # Thread management
        self.executor = ThreadPoolExecutor()

        self.twitch_predictions_lock = Lock()  # Protection
        self.active_betting_site_lock = Lock()

        self.processing_channels = set()
        self.processing_lock = Lock()

    def upload_cookies_to_driver(self, driver):
        """
        Reads and adds cookies to our browser. Refreshes the page when it's done.
        """
        for cookie in self.cookies:
            driver.add_cookie(cookie)
        driver.refresh()

    def _remove_prediction(self, channel):
        """Safely remove a prediction and its associated resources"""
        channel_to_remove = None
        with self.twitch_predictions_lock:
            if channel in self.active_twitch_predictions:
                channel_to_remove = channel
        if channel_to_remove:
            self.remove_drivers(channel_to_remove)
            with self.twitch_predictions_lock:
                del self.active_twitch_predictions[channel_to_remove]
                print(f"Removed expired prediction for {channel}")
        
        # Clean up associated driver if any
    def __del__(self):
        """Ensure proper cleanup of resources
        quit all drivers and shutdown self.executor"""
        pass

    def get_remaining_time(self, channel):
        if channel in self.active_twitch_predictions:
            current_time = time.time()
            end_time = self.active_twitch_predictions[channel]["end_time"]
            remaining_time = max(0, end_time - current_time)
            print("remaining time: ",channel, remaining_time)
            return remaining_time
        return 0

    def check_for_twitch_predictions(self, channel_names, driver, matches_data):
        """
        Check for twitch predictions across multiple channels
        This driver is only used here, but it never gets closed. always open.
        cause were always checking for predictions.
        """
        print("twitch_integration check for predictions")

        # Only start checking if we don't already have an active prediction
        with self.twitch_predictions_lock:
            channels_to_check = [c for c in channel_names if c not in self.active_twitch_predictions]
        # doing it like this with channel_to_check so we don't keep the lock for long
        for channel_to_check in channels_to_check:
        #    futures[self.executor.submit(self._check_channel_for_prediction, channel_to_check, driver, matches_data)] = channel_to_check
            print(f"submitted Checking predictions for {channel_to_check}")
            try:
                self._check_channel_for_prediction(channel_to_check, driver, matches_data)
                #with self.twitch_predictions_lock:  we do this in handle_new_prediction now.
                    #if result:
                        #self.active_twitch_predictions[channel_to_check] = result
                    #elif channel_to_check in self.active_twitch_predictions:
                        #del self.active_twitch_predictions[channel_to_check]
            except Exception as exc:
                print(f'{channel_to_check} generated an exception: {exc}')
                print(traceback.format_exc())


        # Process results as they complete
        #for future in as_completed(futures):


    def _check_channel_for_prediction(self, channel, driver, matches_data):
        """
        Checks if a prediction is active for a given channel.
        creates a new Twitch driver right away
        If one is already tracked, it checks the remaining time (and places a bet if nearly over).
        Otherwise, if an active prediction is detected (via the timer text),
        it offloads the heavy initialization work to handle_new_prediction.
        """
        print(f"check if prediction started for {channel}")

        # First, check if we already have an active prediction for this channel
        with self.twitch_predictions_lock:
            if channel in self.active_twitch_predictions :  # if already active then this block.
                return
        with self.processing_lock:
            if channel in self.processing_channels:
                print("lul")
                return

        try:
            # Navigate to the channel's chat page and check if a timer is running
            driver.get(f"https://www.twitch.tv/popout/{channel}/chat")
            click_points_element(driver)
            click_get_started(driver)
            timer_text = get_timer_text(driver)  # TODO: actually change this because the timer element can also just not exist at all. then

            if timer_text:
                print("timer text", timer_text)
            else:                                # TODO: then this else block gets executed which is weird, it should just be
                print("No timer text found for channel {channel}")
                driver.save_screenshot(f"debug/checkforprediction{channel}.png")
                self.remove_drivers(channel)
                self._remove_prediction(channel)
                return

            if "left to predict" not in timer_text:
                print(f"No active prediction found for {channel}")
                return None

            # Add to processing_channels BEFORE submitting
            with self.processing_lock:
                self.processing_channels.add(channel)

            print(f"Active prediction detected for {channel}. Offloading heavy processing.")
            # Offload the heavy processing work to a separate thread.
            self.executor.submit(self.handle_new_prediction, channel, matches_data)
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error for {channel}: {str(e)}")
            traceback.print_exc()

    def handle_new_prediction(self, channel, matches_data):
        """
        Performs all of the heavy work once a new prediction is detected.
        This includes parsing the timer, clicking through the prediction steps,
        fetching options, calling the OpenAI API to get the match URL, initializing
        the betting site driver, and creating a new Twitch driver for the channel.
        Finally, it schedules a Timer to remove the prediction after it ends.
        """
        try:
            # create a new twitch driver for this channel.
            twitch_channel_driver = create_new_chrome_driver(big=True)  #headless=False)  # TODO: idk if headless or not man.
            twitch_channel_driver.get(f"https://www.twitch.tv/popout/{channel}/chat")
            self.upload_cookies_to_driver(twitch_channel_driver)

            # we do these here instead of right before voting so we have more time then.
            click_points_element(twitch_channel_driver)
            click_get_started(twitch_channel_driver)

            timer_text = get_timer_text(twitch_channel_driver)
            if not timer_text or "left to predict" not in timer_text:
                twitch_channel_driver.save_screenshot(f"debug/AAAAAAAAAAAA_uhmmm.png")
                print("this should never be printed")
                return

            # this needs to be afterwards because thbe timer element will not be the same after we click this.
            click_prediction_button(twitch_channel_driver)
            click_predict_custom_amount(twitch_channel_driver)

            timer = timer_text.split(" left to predict")[0]
            minutes, seconds = map(int, timer.split(':'))
            total_seconds = minutes * 60 + seconds
            end_time = time.time() + total_seconds

            # Use retry-enabled function to get prediction elements
            blue_vote_option, red_vote_option, prediction_question = get_prediction_elements_with_retry(twitch_channel_driver)

            # Call OpenAI function to get match url
            try:
                match_url = get_url_from_openai(
                    prediction_question,
                    [blue_vote_option, red_vote_option],
                    matches_data
                )
            except Exception as e:
                print(f"OpenAI API error for {channel}: {e}")
                twitch_channel_driver.save_screenshot(f"debug/{channel} OpenAI API er.png")
                traceback.print_exc()
                return
            if not match_url:
                print(f"No linked match found for {channel} prediction.")
                return

            # Initialize the betting site driver.
            betting_driver = create_new_chrome_driver()
            betting_driver.get(match_url)
            wait_and_click_all_tab(betting_driver)

            with self.active_betting_site_lock:
                # Check if we already track this betting URL
                if match_url not in self.active_betting_site_data:
                    # Create new betting site entry
                    print(f"New betting match url detected: {match_url}")
                    try:
                        self.active_betting_site_data[match_url] = {
                            "driver": betting_driver,
                            "linked_channels": {channel},
                            "current_odds": None,
                            "last_updated": time.time()
                        }
                    except Exception as e:
                        print(f"Failed to initialize betting site driver: {e}")
                        return
                else:  # because of this, below i need to get the betting_driver again.
                    # Add channel to existing linked channels
                    self.active_betting_site_data[match_url]["linked_channels"].add(channel)
                betting_driver = self.active_betting_site_data[match_url]["driver"]

            # in following line i can use betting_driver ourside of lock because i hope that that is fine. :D
            # TODO: if a problem arises here i can make an own lock for the driver, getting the lock to get the
            #  driver and the driver lock. but im assuming no 2 ones want to use same driver at same time.
            market_name, team1_selector, team2_selector = get_team_odds_selectors(
                betting_driver, blue_vote_option, red_vote_option, prediction_question
            )

            # Prepare prediction data
            prediction_data = {
                "end_time": end_time,
                "bet_placed": False,
                "match_url": match_url,
                "market_name": market_name,
                "team1_selector": team1_selector,
                "team2_selector": team2_selector,
                "blue_option": {
                    "text": blue_vote_option,
                },
                "red_option": {
                    "text": red_vote_option,
                },
                'team1_odds': None,
                'team2_odds': None,
                "twitch_driver": twitch_channel_driver
            }

            # Schedule removal after prediction ends
            Timer(total_seconds, self._remove_prediction, args=[channel]).start()
            print(f"New prediction tracked for {channel}")
            print("added prediction: ", prediction_data)

            # Finally, update the active predictions for this channel.
            with self.twitch_predictions_lock:
                self.active_twitch_predictions[channel] = prediction_data


            # decide the delay before the "starting the driver" task (3 minutes before prediction end)
            #delay_before_driver_start = total_seconds - 180 if total_seconds > 180 else 0
            # make the driver start and do the initialization after the delay

            # decide the delay before starting betting task (1 minute before prediction end)
            #delay_before_betting = total_seconds - 60 if total_seconds > 60 else 0
            #Timer(delay_before_betting, self._place_bet_on_channel, args=[channel]).start()
            # we bet after the delay

        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error for {channel}: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
        finally:
            print("this finally block")
            # Remove from processing_channels, even if errors occurred
            with self.processing_lock:
                if channel in self.processing_channels:
                    self.processing_channels.remove(channel)
                    print("removed from processing channel", channel)

    # TODO: after placing the bet it keeps printing
    #  Match URL https://gg258.bet/en/esports/match/shopify-rebellion-vs-lyon-gaming-02-02 for ltanorth not found. Skipping.
    def update_betting_odds(self):
        # updates the betting site odds.
        """Update betting odds for all active predictions"""
        print("update betting odds")
        futures = {}

        # Thread safety: Get current channels but access their data live
        with self.twitch_predictions_lock:
            active_channels = list(self.active_twitch_predictions.keys())

        # Process each channel, getting fresh data each time
        for channel in active_channels:
            # Retrieve prediction info under twitch_predictions_lock
            with self.twitch_predictions_lock:  # operations in this block need to have the lock and are short.
                # Check if channel is still active and get current data
                if channel not in self.active_twitch_predictions:
                    continue  # skip channel
                twitch_prediction = self.active_twitch_predictions[channel]  # creating a reference
                match_url = twitch_prediction.get("match_url")
                # Get stored not actually selectors from initial prediction setup
                market_name = twitch_prediction.get("market_name")
                team1_selector = twitch_prediction.get('team1_selector')
                team2_selector = twitch_prediction.get('team2_selector')

            with self.active_betting_site_lock:  # operations in this block need to have the lock and are short.
                if match_url not in self.active_betting_site_data:
                    print(self.active_betting_site_data)
                    print(f"Match URL {match_url} for {channel} not found. Skipping.")
                    continue  # skip channel
                site_data = self.active_betting_site_data[match_url]
                betting_driver = site_data.get("driver")
                if not betting_driver:
                    print(f"No driver for {match_url}. Skipping {channel}.")
                    continue  # skip channel

            # Submit the task to update odds
            futures[self.executor.submit(
                get_updated_match_odds,
                betting_driver,
                market_name,
                team1_selector,
                team2_selector
            )] = channel

        # Process results as they complete
        for future in as_completed(futures):
            channel = futures[future]
            try:
                team1_odds, team2_odds = future.result()
                print("following the odds: ", team1_odds, team2_odds)
                with self.twitch_predictions_lock:  # good.
                    # Update with fresh data if channel still active, but dont overwrite valid odds with None.
                    if channel in self.active_twitch_predictions and None not in (team1_odds, team2_odds):
                        print("channel in self.active_twitch_predictions", channel in self.active_twitch_predictions)
                        self.active_twitch_predictions[channel].update({
                            'team1_odds': team1_odds,
                            'team2_odds': team2_odds
                        })
                        print(self.active_twitch_predictions[channel])
                        print(f"Updated odds for {channel}")
                    else:
                        print("sus 1")
            except Exception as exc:
                print(f'Updating odds for {channel} generated an exception: {exc}')
                traceback.print_exc()


    def place_bets(self):
        """Place bets for predictions with less than x seconds remaining"""
        print("placing bets if any")
        futures = {}
        # Thread safety: Get current channels but check times live
        with self.twitch_predictions_lock:
            active_channels = list(self.active_twitch_predictions.keys())
            
        # Check each channel's current time and data
        for channel in active_channels:
            remaining_time = self.get_remaining_time(channel)  # Get remaining time without holding the lock
            print(channel, ": ", remaining_time)
            if remaining_time <= 0: # removes the prediction if not removed yet.
                self._remove_prediction(channel)
                continue
            # Check conditions with lock
            should_place_bet = False
            with self.twitch_predictions_lock:
                if (
                    channel in self.active_twitch_predictions
                    and 0 < remaining_time <= 10  # TODO here too like the todo from above
                    and not self.active_twitch_predictions[channel].get("bet_placed", False)
                ):
                    should_place_bet = True

            # Submit bet placement without holding lock
            if should_place_bet:
                futures[self.executor.submit(self._place_bet_on_channel, channel)] = channel
        for future in as_completed(futures):
            channel = futures[future]
            try:
                future.result()
                print(f"Successfully placed bet for {channel}")
            except Exception as exc:
                print(f'Placing bet for {channel} generated an exception: {exc}')


    def _place_bet_on_channel(self, channel):
        print(f"_place_bet_on_channel:  {channel}")

        # Get fresh prediction data ourselves so we dont need to pass it here
        with self.twitch_predictions_lock:
            if channel not in self.active_twitch_predictions:
                print(f"Prediction ended for {channel}")
                return
            prediction_info = self.active_twitch_predictions[channel]
            if prediction_info.get("bet_placed"):
                print(f"Bet already placed for {channel}")
                return

        # Instead of actual driver operations, just create a dummy driver object

        driver = prediction_info.get('twitch_driver')

        try:
            success = place_bet_on_channel(channel, prediction_info, driver)
            need_cleanup = False
            with self.twitch_predictions_lock:
                if success and channel in self.active_twitch_predictions:
                    self.active_twitch_predictions[channel]["bet_placed"] = True
                    need_cleanup = True
                    print(f"success betting for {channel}")
            # using need_cleanup so i can call remove_drivers outside of the lock.
            if need_cleanup:
                self.remove_drivers(channel)
        finally:
            print(f"finally {channel}")


    def remove_drivers(self, channel):
        """Remove drivers associated with a channel from both twitch predictions and betting sites"""
        self._remove_twitch_driver(channel)
        self._remove_betting_site_driver(channel)

    def _get_linked_betting_url(self, channel):
        """Helper to find the betting URL linked to a Twitch channel"""
        with self.active_betting_site_lock:
            for url, data in self.active_betting_site_data.items():
                if channel in data.get('linked_channels', set()):
                    return url
            return None

    def _remove_twitch_driver(self, channel):
        driver_to_quit = None  # using this so i can quit() outside of lock
        with self.twitch_predictions_lock:
            if channel in self.active_twitch_predictions:
                prediction_data = self.active_twitch_predictions[channel]
                if 'twitch_driver' in prediction_data:
                    driver_to_quit = prediction_data.get('twitch_driver')  # removed "del" call on twitch_driver
        try:
            if driver_to_quit:
                driver_to_quit.quit()
        except Exception as e:
            print(f"Error quitting Twitch driver for {channel}: {e}")

    def _remove_betting_site_driver(self, channel):
        betting_url = self._get_linked_betting_url(channel)
        driver_to_quit = None
        if betting_url:
            with self.active_betting_site_lock:
                if betting_url in self.active_betting_site_data:
                    site_data = self.active_betting_site_data[betting_url]
                    site_data['linked_channels'].discard(channel)  # we discard current channel from linked_channels
                    print("site_data linked channels", betting_url, site_data["linked_channels"])
                    if not site_data['linked_channels']:  # then we check if there is another channel linked
                        if 'driver' in site_data:  # and if not then we can close the driver ourside of lock block
                            driver_to_quit =  site_data['driver']
            try:
                if driver_to_quit:
                    driver_to_quit.quit()
            except Exception as e:
                print(f"Error quitting betting driver for {betting_url}: {e}")
            with self.active_betting_site_lock:
                del self.active_betting_site_data[betting_url]
