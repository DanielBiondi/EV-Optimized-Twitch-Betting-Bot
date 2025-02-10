# point_logic.py

import time
from betting_strategies import calculate_optimal_bet

num_replace = {
    "K": 1000,
    "M": 1000000,
    "B": 1000000000
}


def get_points(current_points): # used in twitch_integratoin.py
    """
    get_points and pure_number work in tandem to return an integer from our displayed channel points.
    :param current_points:
    :return: An integer
    """
    if "K" in current_points:
        num = float(current_points.split("K")[0])
        character = current_points[len(current_points) - 1:]
        current_points = pure_number(string=character, number=num)
    elif "M" in current_points:
        num = float(current_points.split("M")[0])
        character = current_points[len(current_points) - 1:]
        current_points = pure_number(string=character, number=num)
    print("get_points", current_points)
    return int(current_points)


# here, data['blue_team'] will equal to the rivalry.com name of the blue twitch prediction name (believers)
# and data['red_team'] will be equal to the rivalry.com name of the red (doubters) twitch prediction name.
# and match_details are form rivalry
# i hope that blue vores count and red_votes_count is the amount of points voted on that team
def calculate_bet(my_points, blue_votes_count, red_votes_count, blue_odds, red_odds):
    print("calculate_bet with arguments:", my_points, blue_votes_count, red_votes_count, blue_odds, red_odds)

    # Normalize the odds for both teams (odds format)
    normalized_blue_odds, normalized_red_odds = normalize_rivalry_odds(blue_odds, red_odds)

    # Convert normalized odds to probabilities
    p_blue = 1 / normalized_blue_odds
    p_red = 1 / normalized_red_odds

    # Prepare inputs for Kelly Criterion
    true_odds = (p_blue, p_red)
    current_bets = (blue_votes_count, red_votes_count)
    bankroll = my_points

    # Apply Kelly Criterion strategy
    bet_amount, bet_on_blue = calculate_optimal_bet(true_odds, current_bets, bankroll)

    # Determine which team to bet on
    team_to_bet = "blue" if bet_on_blue else "red"

    print("calculated bet", bet_amount, team_to_bet)
    return bet_amount, team_to_bet


def pure_number(string, number):
    """
    :param string: String with an abbreviations for a thousand, million, billion. ("k", "m", "b")
    :param number: Int
    :return: Returns the pure integer without abbreviations or commas for betting.
    """
    mult = 1.0
    if string in num_replace:
        x = num_replace[string]
        mult *= x
        return int(number * mult)


def normalize_rivalry_odds(team1_odds, team2_odds):
    print("normalize rivalry odds with ", team1_odds, team2_odds)
    """
    Normalize the odds for two teams and return the normalized odds.

    :param team1_odds: Odds for Team 1 (e.g., 1.57)
    :param team2_odds: Odds for Team 2 (e.g., 2.19)
    :return: Normalized odds for both teams
    """
    # Step 1: Calculate implied probabilities
    team1_prob = (1 / float(team1_odds)) * 100
    team2_prob = (1 / float(team2_odds)) * 100

    # Step 2: Sum of implied probabilities
    total_prob = team1_prob + team2_prob

    # Step 3: Normalize the probabilities
    normalized_team1_prob = (team1_prob / total_prob) * 100
    normalized_team2_prob = (team2_prob / total_prob) * 100

    # Step 4: Convert back to odds
    normalized_team1_odds = 100 / normalized_team1_prob
    normalized_team2_odds = 100 / normalized_team2_prob

    print("normalized:", normalized_team1_odds, normalized_team2_odds)
    return normalized_team1_odds, normalized_team2_odds

