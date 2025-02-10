# use_openai.py
import os
import random
import time

import google.generativeai as genai
import json

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


response_schema_for_url = {
    "type": "OBJECT",
    "properties": {
        "reasoning": {"type": "STRING"},
        "url": {"type": "STRING"}

    },
    "required": ["reasoning" ,"url"]
}
generation_config_for_url = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
  "response_schema": response_schema_for_url
}
model_for_url = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config_for_url,
)

########################################## different configs ######

response_schema_selectors = {
    "type": "OBJECT",
    "properties": {
        "reasoning": {"type": "STRING"},
        "market_name": {"type": "STRING"},
        "market_id": {"type": "STRING"},
        "twitch_team_1_name": {"type": "STRING"},
        "twitch_team_1_id": {"type": "STRING"},
        "twitch_team_2_name": {"type": "STRING"},
        "twitch_team_2_id": {"type": "STRING"}
    },
    "required": [
        "reasoning",
        "market_name",
        "market_id",
        "twitch_team_1_name",
        "twitch_team_1_id",
        "twitch_team_2_name",
        "twitch_team_2_id"
    ]
}
generation_config_for_selectors = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
    "response_schema": response_schema_selectors
}
model_for_selectors = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config_for_selectors,
)

# the LLM returns a json object like this:
#{
#  "url": "https://www.rivalry.com/match/league-of-legends/world-championship/1298108-lng-vs-weibo",
#}


# Use OpenAI's GPT to parse team names and match them to rivalry.com data.
def get_url_from_openai(prediction_question, vote_options, matches_data, max_retries=5):
    print("get_url_from_openai_start",prediction_question, vote_options, matches_data)
    for attempt  in range(max_retries):  # Try 3 times total
        try:
            chat = model_for_url.start_chat(history=[])
            prompt = (f"FOR TESTING RIGHT NOW: IF NONE FIT, WRITE ONE OF THEM ANYWAYS"
                      f"You are an assistant that processes Twitch prediction polls and match data to determine relevant betting information.\n\n**Given the following Twitch prediction:**\n\n```\nPrediction question: {prediction_question}\nVote options:\n{vote_options}\n```\n\n**And the following match data:**\n\n{matches_data}\n\n**Your task is to:**\n\n1. Identify which match from the match data corresponds to the Twitch prediction.\n2. Use the team names from the match data (not from the Twitch prediction).\n2.5 Use the odds from the Twitch prediction.\n3. Output the information in an easily parsable JSON format with the following key:\n - `url`\n **Note:**\n\n- Ensure that the team names are taken from the match data provided.\n- The output should be valid JSON that can be easily parsed by a program.\n- If multiple matches could correspond to the prediction, choose the most relevant one based on the team names and context. Also if no match corresponds to the prediction, then return no url. return reasoning and url in the json seperately NVM always return one of them for testing. also i guess for testing its better if oyu dont choose the first one.\n\n---\n")
            response = None
            try:
                response = chat.send_message(prompt)
            except Exception as e:  # google.api_core.exceptions.ResourceExhausted
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                    print(f"Resource exhausted, retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    print("Max retries reached. Giving up.")
                    raise  # Re-raise the exception after max retries
            response_json = json.loads(response.text)  # # Convert JSON to Python dict
            print("data: ",response_json)
            url = response_json["url"]


            #return "https://gg258.bet/en/esports/match/fire-bloom-vs-team-lynx-31-01"
            return url  # TODO OBVIOUSLY UNCOMMENT THIS LINE AND DELETE ABOVE LINE!!!!
        except (KeyError, json.JSONDecodeError):
            continue  # Try again if failed
    return None


def get_twitch_team_selectors(market_names_and_titles, twitch_team1_name, twitch_team2_name, prediction_question):
  """Uses LLM to find betting elements matching Twitch teams and prediction context"""

  # Create mappings for ID lookups and generate IDs
  market_id_to_name = {}
  option_id_to_title = {}
  markets = {}

  # Use market_name as key to generate unique market IDs
  unique_market_names = set()
  for market_tuple in market_names_and_titles:
    unique_market_names.add(market_tuple["market_name"])

  market_name_to_id = {name: f"market_{i}" for i, name in enumerate(unique_market_names)}

  # Generate option IDs and structure the market data
  option_counter = 0
  for market_tuple in market_names_and_titles:
    market_name = market_tuple["market_name"]
    market_id = market_name_to_id[market_name]
    title = market_tuple["title"]
    option_id = f"option_{option_counter}"
    option_counter += 1

    if market_id not in markets:
      markets[market_id] = {
        "market_name": market_name,
        "options": []
      }
    markets[market_id]["options"].append({
      "option_id": option_id,
      "title": title
    })

    # Create ID mappings for final lookup
    market_id_to_name[market_id] = market_name
    option_id_to_title[option_id] = title

  # Format markets into readable string with IDs
  formatted_markets = []
  for market_id, market_data in markets.items():
    option_lines = "\n".join([
      f"    - Option ID: {opt['option_id']}, Title: {opt['title']}"
      for opt in market_data["options"]
    ])
    formatted_markets.append(
      f"- Market ID: {market_id}, Name: {market_data['market_name']}\n"
      f"  Options:\n{option_lines}"
    )
  formatted_markets_str = "\n".join(formatted_markets)

  # Construct the LLM prompt
  prompt = f"""You are an assistant that matches Twitch prediction questions to betting markets. Follow these steps:

1. Analyze the prediction question to determine the relevant betting market (e.g., "Map 1 - Winner", "Series Winner"). If unspecified, assume it refers to the current map or if no current map then next map.
2. Match the Twitch team names to the titles in the selected market's options. Consider possible name variations (abbreviations, different casing, the twitch streamer being creative.).
3. Return JSON with: 
"reasoning":(about 2 sentences), 
"market_name": the exact market name, 
"market_id": Selected market's ID (starts with "market_", exactly like its written above),  
"twitch_team_1_name": betting site name for twitch team1,
"twitch_team_1_id": Option ID for {twitch_team1_name} (starts with "option_", exactly like its written above), 
"twitch_team_2_name": betting site name for twitch team2,
"twitch_team_2_id": Option ID for {twitch_team2_name} (starts with "option_", exactly like its written above)

**Available Markets:**
{formatted_markets_str}

**Twitch Teams:**
- Team 1: {twitch_team1_name}
- Team 2: {twitch_team2_name}

**Prediction Question:** "{prediction_question}"

Use null for unmatched fields. NVM always return one of each for testing. 
IMPORTANT: FOR TESTING RIGHT NOW: IF NONE FIT, WRITE ONE OF THEM ANYWAYS"""


  try:
    # Get structured response from LLM
    chat = model_for_selectors.start_chat(history=[])
    response = chat.send_message(prompt)
    json_response = json.loads(response.text)  # Response will already be in JSON format
    print(json_response)

    # Extract IDs from response
    market_id = json_response.get("market_id")
    team1_id = json_response.get("twitch_team_1_id")
    team2_id = json_response.get("twitch_team_2_id")

    # Convert IDs to the strings using mappings
    market_name = market_id_to_name.get(market_id)
    team1_title = option_id_to_title.get(team1_id)
    team2_title = option_id_to_title.get(team2_id)

    return market_name, team1_title, team2_title
  except Exception as e:
    print(f"Error in get_twitch_team_selectors: {str(e)}")
    return None, None, None

  # TODO: "NVM always return one of" i have that in the prompts and its just for testing delete that.
