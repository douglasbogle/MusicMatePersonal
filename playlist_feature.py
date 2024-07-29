import requests
import sys
# Imports SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
from get_spotify_api_key import *
import urllib.parse
from datetime import datetime
from flask import Flask, redirect, request, session, url_for, jsonify
from dotenv import load_dotenv

# Load environmental variables from .env
load_dotenv()

# Load necessary access token's etc. for API
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
BASE_URL = 'https://api.spotify.com/v1/'
AUTH_URL = 'https://accounts.spotify.com/authorize'
# Change based on where you're hosting webiste
REDIRECT_URI = 'https://musicmatepersonal.pythonanywhere.com/callback'
TOKEN_URL = 'https://accounts.spotify.com/api/token'


def get_spotify_auth_url():
    """
    Called after logging in, gets spotify's auth page url so user can grant us access to their Spotify account.
    """
    scope = 'playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-read-private'

    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True,
    }

    auth_url = f'{AUTH_URL}?{urllib.parse.urlencode(params)}'
    return auth_url


def get_token_info(auth_code):
    """
    Part of OAuth flow for Spotify, gets us an access token to use in our API calls to get info about the current user.
    """
    request_body = {
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(TOKEN_URL, data=request_body)
    return response.json()


def refresh_token():
    """
    Refreshes user's access token if it expires.
    """
    if 'refresh_token' not in session:
        return redirect(url_for('dashboard'))

    if datetime.now().timestamp() > session['expires_at']:
        request_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        }

        response = requests.post(TOKEN_URL, data=request_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + \
            new_token_info['expires_in']

        return redirect(url_for('dashboard'))


def get_user_info():
    """
    Uses Spotify API's 'me' method to get info about current user.
    """
    if 'access_token' not in session:
        return redirect(url_for('dashboard'))

    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))

    headers = {
        "Authorization": f"Bearer {session['access_token']}",
    }

    response = requests.get(BASE_URL + 'me', headers=headers)
    return response.json()


def get_user_playlists():
    """
    Uses Spotify API's me/playlists method to get the current user's playlists.
    """
    if 'access_token' not in session:
        return None

    if datetime.now().timestamp() > session['expires_at']:
        refresh_token()

    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }

    response = requests.get(BASE_URL + 'me/playlists', headers=headers)

    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        print(response.txt)
        return {"error": response.json().get('error', 'Unknown error occurred')}


def create_playlist_helper(name, description, public):
    """
    Sends POST request to Spotify API to create a playlist for the active user from our webpage.
    """
    user_info = get_user_info()
    user_id = user_info['id']

    if 'access_token' not in session:
        return redirect(url_for('dashboard'))

    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))

    headers = {
        "Authorization": f"Bearer {session['access_token']}",
        "Content-Type": "application/json"
    }

    data = {
        'name': name,
        'description': description,
        'public': public,
    }

    response = requests.post(
        BASE_URL + f'users/{user_id}/playlists', headers=headers, json=data)
    return response.json()


def add_to_playlist_helper(playlist_id, track_uri):
    """
    Sends a POST request to Spotify API to add a song to current user's Spotify playlist.
    """
    if 'access_token' not in session:
        return redirect(url_for('dashboard'))

    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for(refresh_token))

    headers = {
        "Authorization": f"Bearer {session['access_token']}",
        "Content-Type": "application/json",
    }

    data = {
        'uris': [track_uri]
    }

    response = requests.post(
        BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers, json=data)

    if response.status_code == 200:
        return response.json()  # Success, return the response JSON
    else:
        return {"error": response.json().get('error', 'Unknown error occurred')}
