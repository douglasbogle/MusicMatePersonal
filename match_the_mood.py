import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
# Imports SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
from get_spotify_api_key import *
from songs import *
from match_the_day import recommend_songs


# Get API keys from environment variables
load_dotenv()
GPT_API_KEY = os.getenv('GPT_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


# Uses OpenAI API to get some query words based on a user's mood
def gpt_query_words_mood(mood, api_key):
    """
    Function to generate spotify search method query words using Openai API GPT-3.5 Turbo based on user's mood
    """
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a spotify genius that specializes in finding the right playlist based off some information. Generate a list of 3 - 5 words or short phrases to use in the Spotify API search function to search for a playlist based on the given mood."},
            # Consider changing to get better responses
            {"role": "user", "content": f"I am feeling {mood}."}
        ]
    )
    return completion.choices[0].message.content


# Essentially the main function to utilize all the former functions
def get_songs_from_mood(mood, genre):
    """
    Main functionality for match the mood feature, calls other necessary functions
    """
    query_words = gpt_query_words_mood(mood, GPT_API_KEY)
    songs = recommend_songs(query_words, genre)
    return songs, mood  # return these to be used by match_the_mood.html
