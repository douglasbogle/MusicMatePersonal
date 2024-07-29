import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
# Imports SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
from get_spotify_api_key import *
from songs import *  # Import functions from songs.py


# Get API keys from environment variables
load_dotenv()
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GPT_API_KEY = os.getenv('GPT_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


def weather_forecast(city, api_key):
    """
    Given a city entered in by the user, requests weather data such as temperature and a short description.
    """
    url = f'http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}'
    response = requests.get(url)

    if response.status_code == 200:
        json_response = response.json()
        city_from_response = json_response['location']['name']
        region_from_response = json_response['location']['region']
        fahrenheit = json_response['current']['temp_f']
        weather = json_response['current']['condition']['text']
        return (fahrenheit, weather), city_from_response
    else:
        return None, None


def gpt_query_words(weather_stats, activity, api_key):
    """
    Function to generate spotify search method query words using Openai API GPT-3.5 Turbo based on weather, activity, and genre
    """
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a spotify genius that specializes in finding the right playlist based off some information. Generate a list of 3 - 5 words or short phrases to use in the Spotify API search function to search for a playlist based on the given information."},
            {"role": "user",
                "content": f"The weather is {weather_stats[0]} degrees and {weather_stats[1]} and the activity is {activity}."}
        ]
    )
    return completion.choices[0].message.content


def recommend_songs(query_words, genre):
    """
    Uses gpt's query words to make a search spotify, randomly selects a playlist and then randomly selects six songs from this playlist.
    """
    playlist = get_playlist_from_spotify(query_words, genre)

    songs = get_songs_from_playlist(genre, playlist)

    all_songs = list(songs.values())
    random_6_songs = random.sample(all_songs, k=min(6, len(all_songs)))

    random_6_songs_dict = {}
    for i, song in enumerate(random_6_songs):
        random_6_songs_dict[i + 1] = {
            "song_name": song["song_name"],
            "artist_name": song["artist_name"],
            "album_name": song["album_name"],
            "song_link": song["song_link"],
            "album_cover": song["album_cover"],
            "popularity": song["popularity"],
            "uri": song["uri"]
        }
    return random_6_songs_dict


def get_songs_from_activity(city, activity, genre):
    """
    Holds main functionality for match the day feature.
    """
    weather_stats, city_name = weather_forecast(city, WEATHER_API_KEY)
    if not weather_stats or not city_name:
        return None, None
    query_words = gpt_query_words(weather_stats, activity, GPT_API_KEY)
    songs = recommend_songs(query_words, genre)

    # get activity from session in app.py, use all this for match_the_mood.html
    return songs, weather_stats
