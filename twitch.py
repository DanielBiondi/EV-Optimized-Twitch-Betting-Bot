# twitch.py

from twitch_integration import TwitchIntegration

class TwitchHandler:

    def __init__(self):# removed webdriver.Chrome() in signiture
        self.integration = TwitchIntegration()

    @property
    def active_predictions(self):
        # Acquire lock to ensure we see the latest state
        with self.integration.twitch_predictions_lock:
            return self.integration.active_twitch_predictions


    def check_for_twitch_predictions(self, channel_names, driver, matches_data): # get twitch predictons
        self.integration.check_for_twitch_predictions(channel_names, driver, matches_data)

    def update_odds(self):
        self.integration.update_betting_odds()

    def place_bets(self):
        self.integration.place_bets()
