import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
# Imports SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
from get_spotify_api_key import *
from songs import *  # Import functions from songs.py


# Get similar songs feature
def get_similar_songs(song):
    """
    This feature is really just a Spotify API call for similar songs to the user entered song. Calls the function that does this.
    """
    return get_similar(song, limit=6)
