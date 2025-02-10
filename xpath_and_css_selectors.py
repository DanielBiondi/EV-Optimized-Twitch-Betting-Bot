# xpath_and_css_selectors.py
"""
This file is for all relevant locators
"""
#daniel
actual_prediction_button_xpath = "//button[.//*[@data-test-selector='predictions-list-item__subtitle' and contains(text(),'left to predict')]]"
# daniel)
channel_points_button = '/html/body/div[1]/div/div[1]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div/div[1]/div[2]/button'
# daniel this one is right after clicking points this is not the timer after clicking prediction.
prediction_timer_xpath = '/html/body/div[1]/div/div[1]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div[6]/div/button/div/div[2]/p[2]'

# daniel
get_started_button = '//*[@id="channel-points-reward-center-body"]/div/button'

# daniel
points_text_xpath = '//div[@data-test-selector="copo-balance-string"]/span'

# daniel prediction x button: (to close out of hte prediciton window. need to click on the pionts again)
x_button = '/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[1]/div[1]/div/div[4]/button'

# daniel prediction back button (to go when you clicked on the points thing):
prediction_back_button_xpath = "/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[1]/div[1]/div/div[1]/button"

# daniel blue vote option By.CSS_SELECTOR:
blue_vote_option_BYCSS = "div[style*='color: rgb(56, 122, 255)'] p.tw-title"

# daniel blue vote option: example: (Team Falcons)
#blue_vote_option_xpath = "/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[1]/div/p"

# daniel red vote option By.CSS_SELECTOR:
red_vote_option_BYCSS = "div[style*='color: rgb(245, 0, 155)'] p.tw-title"

# daniel red vote option: example: (Team Spirit)
#red_vote_option_xpath = "/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/p"

#daniel prediction question By.CSS_SELECTOR:
prediction_question_BYCSS = "div.prediction-checkout-details-header p.tw-title"

# daniel prediction question: example: (1 MAP WINNER)
#prediction_question_xpath = "/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[1]/p[1]"

blue_votes = '/html/body/div[1]/div/div[1]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[3]/div[1]/div[1]/div/div/div[2]'

red_votes = '/html/body/div[1]/div/div[1]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[1]/div/div/div[2]	'

blue_field = '/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[3]/div[1]/div/div/div[1]/div/div/div/div/input'

red_field = "/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[3]/div[1]/div/div/div[2]/div/div/div/div/input"

blue_button = '/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[3]/div[1]/div/div/div[1]/div/div/button'

red_button = '/html/body/div[1]/div/div[1]/div/div[2]/div/div[1]/aside/div/div/div[2]/div/div/section/div/div[6]/div[2]/div[2]/div[1]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div/div/div/div/div[3]/div[1]/div/div/div[2]/div/div/button'

