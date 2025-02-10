import math


def calculate_optimal_bet(true_odds, current_bets, bankroll):
    """
    Calculate optimal bet amount using EV maximization and Kelly criterion as safety.

    Args:
        true_odds (tuple): (p_blue, p_red) true probabilities
        current_bets (tuple): (blue_votes, red_votes) current bet distribution
        bankroll (float): Available points to bet

    Returns:
        tuple: (bet_amount, bet_on_blue) where bet_on_blue is boolean
    """
    p_blue, p_red = true_odds
    blue_votes, red_votes = current_bets

    # First determine which side has positive EV
    if blue_votes + red_votes == 0:
        return 0, True
    if blue_votes == 0 and red_votes > 10 and bankroll >= 10:
        bet = 10
        return bet, True  # bet on blue (which has 0 points)
    if red_votes == 0 and blue_votes > 10 and bankroll >= 10:
        bet = 10
        return bet, False  # bet on red (which has 0 points)
    if p_blue > blue_votes / (blue_votes + red_votes):
        # Bet on blue
        win_prob = p_blue
        initial_our_side = blue_votes
        total_difference = red_votes
        bet_on_blue = True
    else:
        # Bet on red
        win_prob = p_red
        initial_our_side = red_votes
        total_difference = blue_votes
        bet_on_blue = False

    loss_prob = 1 - win_prob

    # Calculate optimal X using derivative of EV formula
    # From: EV = (win_prob * total_difference * X)/(initial_our_side + X) - loss_prob * X
    # Derivative set to 0 gives us:
    optimal_x = math.sqrt((win_prob * total_difference * initial_our_side) / loss_prob) - initial_our_side

    # Apply Kelly criterion as safety check
    # Kelly fraction = (p*b - q)/b where b is odds-1, p is win prob, q is loss prob
    current_odds = total_difference / initial_our_side
    kelly_fraction = (win_prob * current_odds - loss_prob) / current_odds
    kelly_bet = bankroll * kelly_fraction

    # Take the minimum of:
    # 1. Optimal X from EV formula
    # 2. Kelly bet
    # 3. Max bet limit
    # 4. Available bankroll
    final_bet = min(optimal_x, kelly_bet, 250000, bankroll)

    # Don't bet if EV is negative
    if final_bet <= 0:
        return 0, True
    final_bet = round(final_bet)
    return final_bet, bet_on_blue
