#import yappi
import asyncio

from utils import create_new_chrome_driver
from twitch import TwitchHandler
from betting_website_scraping import scrape_with_retry
from config import CONFIG

async def main():
    twitch_check_for_new_predictions_driver = None
    try:
        twitch_check_for_new_predictions_driver = create_new_chrome_driver()

        # TODO: upload cookies here
        twitch_handler = TwitchHandler()

        # Navigate to Twitch and upload cookies
        twitch_check_for_new_predictions_driver.get("https://www.twitch.tv/popout/revolta/chat?popout=")
        twitch_handler.integration.upload_cookies_to_driver(twitch_check_for_new_predictions_driver)

        channel_names = CONFIG.get("twitch_channels", [])

        matches_data = scrape_with_retry()

        tasks = [
            asyncio.create_task(place_bets_continuously(twitch_handler)),
            asyncio.create_task(update_odds_periodically(twitch_handler)),
            asyncio.create_task(check_predictions_periodically(
                twitch_handler,
                channel_names,
                twitch_check_for_new_predictions_driver,
                matches_data
            ))
        ]
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as e:
        print("Exception occurred:", e)
    finally:
        print("finally block")
        if twitch_check_for_new_predictions_driver:
            twitch_check_for_new_predictions_driver.quit()

async def check_predictions_periodically(twitch_handler, channel_names, driver, matches_data):
    """Checks for new predictions every 20 seconds, offloading blocking calls to threads"""
    loop = asyncio.get_event_loop()
    while True:
        try:
            # Offload the blocking Selenium call to a thread
            await loop.run_in_executor(
                twitch_handler.integration.executor,
                twitch_handler.check_for_twitch_predictions,
                channel_names,
                driver,
                matches_data
            )
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in check_predictions_periodically: {e}")

async def place_bets_continuously(twitch_handler):
    """Highest priority task that places bets every second"""
    loop = asyncio.get_event_loop()
    while True:
        try:
            if twitch_handler.active_predictions:
                # Offload bet placement to a thread if it involves Selenium
                await loop.run_in_executor(
                    twitch_handler.integration.executor,
                    twitch_handler.place_bets
                )
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in place_bets_continuously: {e}")

async def update_odds_periodically(twitch_handler):
    """Updates odds every 5 seconds using threads for Selenium"""
    loop = asyncio.get_event_loop()
    while True:
        try:
            if twitch_handler.active_predictions:
                await loop.run_in_executor(
                    twitch_handler.integration.executor,
                    twitch_handler.update_odds
                )
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error in update_odds_periodically: {e}")

# TODO: make that it periodicalls like every 30mins updates the main betting website url list.
#  either this or restart the whole main program every hour or so. depends on if I think

# TODO: make that when a prediction is found instead of opening the driver immediately four different Timers: one 3 minutes
#  before the prediction ends open the betting website driver and start updating odds, 1 minute before start the twitch
#  driver, and 5 or 10 seconds before place the bet, and the timer for removing the bet that i already have.
#  that would make the average cpu and ram usage go down in those moments.

# TODO: another resource optimizing thing i could do would be to check wich streams are even on by seeing which chats
#  are active or not. if a chat is not active then delete it from the list of channels and only add it after delay of
#  10 mins or so.

# TODO: could add a feature so it would also work on channels that the user marks as "cancels predictions". Then, we
#  would need to check on the betting website if the game timer started (after reloading), and then when we see that it
#  started then we place the bet regardless of timer. Pretty complicated to implement, and I do not really care for it.
#  also the user would need to mark them himself. if not, technically it would be possible for the program to mark them
#  if the prediction is cancelled often enough relative to amount of bets. again, I do not care much about this feature.

if __name__ == "__main__":
    # Start Yappi profiler. The "profile_threads=True" option will profile threads as well.
   # yappi.start(profile_threads=True)
   # try:
    asyncio.run(main())
    """except KeyboardInterrupt:
            # KeyboardInterrupt may be handled both inside main and here.
            print("Main application interrupted by user.")
    finally:
        # Stop yappi profiler
        yappi.stop()

        # Retrieve function stats and print them.
        print("\nYappi function stats:")
        func_stats = yappi.get_func_stats()
        # Uncomment the following line to print in a columnized format in your terminal.
        func_stats.print_all()

        # Optionally, print thread stats as well:
        print("\nYappi thread stats:")
        thread_stats = yappi.get_thread_stats()

        #thread_stats.print_all()
        func_stats = yappi.get_func_stats()
        my_stats = [f for f in func_stats if "main.py" in f.full_name or "twitch" in f.full_name or
                    "betting_website" in f.full_name or "use_openai.py" in f.full_name or "betting_strategies" in f.full_name
                    or "point_logic" in f.full_name]
        for stat in my_stats:
            print(stat)

        # Optionally, you can save stats to a file (for example in Callgrind format) with:
        func_stats.save("profile_stats.callgrind", type="callgrind")
"""
