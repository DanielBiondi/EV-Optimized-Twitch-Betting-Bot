# EV-Optimized-Twitch-Predictions-Bot - Smart Expected Value Optimizing Twitch Prediction Betting Bot

[![MIT License Badge](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version Badge](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

## What is EV-Optimized-Twitch-Predictions-Bot?

EV-Optimized-Twitch-Predictions-Bot is an automated betting program designed to intelligently participate in Twitch channel predictions.  It leverages real-time odds from external betting websites, advanced mathematical calculations, and a fast language model to identify profitable betting opportunities and place optimal bets, maximizing your potential to earn Twitch channel points.

**In simple terms:** This bot watches Twitch predictions, finds good bets based on real-world odds, and automatically bets for you, aiming to increase your channel points using a smart strategy. It can run 24/7, even when you're not around!

## How Twitch Betting Predictions Work (For New Users)

Many Twitch streamers use the "Predictions" feature to engage their audience during streams, especially for esports or competitive events. Here's a quick rundown:

1.  **Streamer Starts a Prediction:** The streamer poses a question with two or more possible outcomes (e.g., "Will Team A win vs. Team B?").
2.  **Voting Period:** Viewers have a limited time to "vote" by predicting one of the outcomes and staking their channel points.
3.  **Outcome and Payout:** After the event, the streamer declares the correct outcome. Viewers who predicted correctly receive a payout of channel points, multiplied by the odds displayed at the time of the prediction.  *Higher odds mean lower probability, thus a higher payout if correct.*

**Why Automate?**

The primary reasons for automating Twitch prediction betting are:

*   **24/7 Operation:**  The *most significant* advantage is that you don't need to be present. You can let the bot run continuously on your favorite channels, maximizing opportunities to earn points while you're doing other things. 
*   **Speed and Precision:** Manually monitoring multiple channels, analyzing odds, and placing bets within the short time windows is extremely difficult, even if you're actively watching. This is further complicated by the fact that odds can change rapidly, requiring constant re-evaluation and quick reactions, something humans struggle with but automation excels at.
*   **Optimal Strategy:**  The bot uses precise mathematical calculations to determine the best bet size and placement, potentially outperforming even people with similar strategies.
* **Concurrency:** Easily participate in multiple channels and take part in multiple predictions simultaneously.
*   **Eliminates Human Error:**  Removes the risk of misclicks, delays, or emotional decision-making that can affect manual betting.

## How EV-Optimized-Twitch-Predictions-Bot Works: The Strategy

EV-Optimized-Twitch-Predictions-Bot employs a sophisticated strategy to identify and capitalize on profitable betting opportunities:

1.  **Real-Money Odds Scraping:** The bot scrapes odds data from a real-money betting website.  *Currently, only GG258.bet links are supported*. You can specify the exact GG258.bet link for the game you want to track in the `config.yaml` file. This website offers odds that reflect the broader betting market's assessment of the probability of each outcome.

2.  **Fast LLM for Match Matching:**  Twitch predictions often use slightly different team names or phrasing than betting websites. To bridge this gap, the bot utilizes a fast and cheap Language Model (LLM) API (currently Gemini 2.0 Flash) to intelligently match the Twitch prediction question and team names with the correct match and betting markets on GG258.bet. This ensures we're comparing apples to apples.

3.  **Expected Value (EV) Calculation:** The core strategy maximizes Expected Value and uses the Kelly Criterion for bet sizing. The bot:

    *   **Normalizes Odds:** Normalizes GG258.bet's odds to remove the "vig" (house edge).
    *   **Calculates Implied Probabilities:** Converts normalized odds to probabilities (`p_blue`, `p_red`).
    *   **Determines Favorable Side:** Identifies the side with a higher implied probability than the current Twitch vote proportion.
       *   **Calculates Optimal Bet (EV Maximization):** Calculates the bet size (`X`) that maximizes Expected Value, *before* applying risk management.  This is a crucial step because, unlike traditional betting scenarios, the act of placing a bet on Twitch *changes the odds*.  Therefore, we need a formula that accounts for this dynamic.  The bot uses the derivative of the EV formula:

        ```
        EV = (win_prob * total_difference * X) / (initial_our_side + X) - loss_prob * X
        ```
        Where:
          * `win_prob`: Probability of our chosen side winning.
          * `loss_prob`: Probability of our chosen side losing (1 - `win_prob`).
          * `initial_our_side`:  Points bet on our side *before* our bet.
          * `total_difference`: Points bet on the *opposite* side.
          * `X`:  Our bet size.

        By taking the derivative of this EV formula with respect to `X` and setting it to zero, we can find the bet size (`optimal_x`) that maximizes the Expected Value. This gives us:

        ```
    *   **Applies Kelly Criterion (Risk Management):** The Kelly Criterion optimizes for long-term growth and manages risk:

        ```
        kelly_fraction = (win_prob * current_odds - loss_prob) / current_odds
        kelly_bet = bankroll * kelly_fraction
        ```

    *   **Final Bet:** The final bet is the minimum of these values:

        ```
        final_bet = min(optimal_x, kelly_bet, 250000, bankroll)  // 250000 is the maximum bet on Twitch
        ```
4.  **Automated Betting:** Once a positive EV bet is identified, the bot automatically places the calculated bet on Twitch, *typically in the last few seconds of the prediction window*, ensuring you capitalize on the opportunity quickly.

**Technical Details (For the Curious):**

*   **Selenium Automation:** The bot uses Selenium to automate browser interactions with both Twitch and the betting website.
*   **Asynchronous Architecture:**  The program is built using `asyncio` and threading for efficient concurrent operation.  It simultaneously:
    *   Monitors multiple Twitch channels for predictions.
    *   Updates betting odds periodically.
    *   Places bets promptly when opportunities arise.
*   **Robust Error Handling and Retries:** The bot includes retry mechanisms for website scraping and other operations that have failed before, to handle network issues and website hiccups.

## Features

*   **Automated Twitch Prediction Betting:** Hands-free betting on Twitch predictions.
*   **Positive Expected Value (EV) Strategy:**  Intelligent betting based on real-world odds and mathematical calculations.
*   **Real-time Odds Scraping:**  Fetches up-to-date odds from GG258.bet.
*   **LLM-Powered Match Identification:** Accurately links Twitch predictions to betting website matches using Gemini 1.5 Flash.
*   **Optimal Bet Sizing:** Calculates the ideal bet amount based on your channel points and EV.
*   **Multi-Channel Monitoring:** Can monitor predictions across multiple Twitch channels simultaneously.
*   **Fast and Efficient:** Asynchronous and threaded architecture for optimal performance.
*   **Configurable:**  Allows customization via a configuration file (see below).

## Getting Started: Installation and Setup

Follow these steps to get EV-Optimized-Twitch-Predictions-Bot up and running:

**Prerequisites:**

1.  **Python 3.12:**  This project works on Python version 3.12.
2.  **Google Chrome Browser:** The bot uses Google Chrome.
3.  **ChromeDriver:**  Download the ChromeDriver that matches your Chrome version from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads). Place it in a directory that is in your system's `PATH`, or specify the path in `config.yaml`.

**Installation:**

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/DanielBiondi/EV-Optimized-Twitch-Predictions-Bot.git
    cd EV-Optimized-Twitch-Predictions-Bot
    ```
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```
3.  **Activate the Virtual Environment:**
    *   **Windows:** `venv\Scripts\activate`
    *   **macOS/Linux:** `source venv/bin/activate`
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

**Configuration:**

1.  **`config.yaml` File:**  Create a `config.yaml` file in the project root directory (if it doesn't exist - you should provide a `config.yaml.example`). This file is used to configure the bot.  Here's an example structure:

    ```yaml
    twitch_channels:
      - streamer1
      - streamer2
      - streamer3
    betting_website_url: "https://gg258.bet/en/betting/esports/league-of-legends"
    chromedriver_path: ""  # Optional if chromedriver is in PATH
    ```

    *   **`twitch_channels`:**  A list of Twitch channel names.
    *   **`betting_website_url`:** The URL of the *specific* GG258.bet page for the game you want to track (e.g., League of Legends, CS:GO).
    *   **`chromedriver_path`:** (Optional) Path to your ChromeDriver if it's not in your system's `PATH`. If not given and chromedriver not in PATH, then the program should install the right chromedriver every time you start it.

2.  **Twitch Cookies (Authentication):**
    *   **How to Get Cookies:**
        1.  Log in to Twitch in your Chrome browser.
        2.  Install a browser extension to export cookies (e.g., "EditThisCookie" for Chrome).
        3.  Export your Twitch cookies as a *CSV* file, naming it *exactly* `twitch_cookies.csv`.
        4.  Place this `twitch_cookies.csv` file in the project root directory.
        5. **Important**: The `twitch_cookies.csv` is in the .gitignore, to prevent you from accidentally committing your cookies. Make sure you *create* the `twitch_cookies.csv` file in the root of your project.

3.  **Google Gemini API Key (Environment Variable):**
    *   **You *must* set your Google Gemini API key as an environment variable.**  Do *not* put it directly in the `config.yaml` file.
    *   **Example (Windows Command Prompt):** `set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE`
    *   **Example (Windows PowerShell):** `$env:GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"`
    *   **Example (Linux/macOS):** `export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"`
    * Obtain your Google API key here: [https://ai.google.dev/](https://ai.google.dev/)

## Usage

1.  **Run the Bot:**
    ```bash
    python main.py
    ```

2.  **Monitoring:**  The bot will start monitoring the configured channels. Console output will indicate:
    *   Channels being monitored.
    *   Detected predictions.
    *   Betting decisions and placements.
    *   Odds updates.
    *   Errors.

3.  **Stop the Bot:** Press `Ctrl+C` to stop gracefully (closes drivers).

## Program Restrictions

*   **Premature Betting Window Closure:** Streamers can manually close the betting window before the scheduled end time (e.g., right as a game starts). The bot currently doesn't detect this, which can lead to missed betting opportunities.

## Potential Improvements and Future Features

*   **Premature Closure Detection:**  Add functionality to monitor a separate list of channels known for premature prediction closure.  The bot could check the betting website to determine if the game has started, and start the betting then.
*   **Early Betting Strategy:** For predictions with high confidence and significant point pools, implement an "early betting" option.  This would place a smaller bet earlier in the prediction window to influence the Twitch odds, potentially increasing the payout if the prediction is correct. (This is only beneficial in specific high-volume scenarios.)
*   **Different Betting Strategies:** Implement and allow users to choose from different betting strategies.
*   **Advanced Error Handling and Logging:**  Improve error reporting and logging.
*   **Customizable Bet Sizing Parameters:** Allow users to fine-tune risk tolerance.

## Important Notes and Disclaimer

*   **Use at Your Own Risk:** This bot is provided as-is, for educational and experimental purposes only.
*   **Websites can change:** When websites change in some ways, the bot can stop working until updated.
*   **Google Gemini API Costs:** Be mindful of your Google Gemini API usage and costs, certain amounts of Gemini 2.0 Flash should be free.
*   **ChromeDriver Compatibility:** Ensure your ChromeDriver version matches your Chrome browser version.
*   **Cookie Management:** Handle your Twitch cookies securely and avoid sharing them.

## Contributing

Contributions are welcome! See the `LICENSE` file for details.
