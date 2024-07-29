import sqlite3
from dotenv import load_dotenv
import os
from songs import *
load_dotenv()


def get_db_connection():
    """
    Function to connect to SQLite database.
    """
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows fetching rows as dictionaries
    return conn


def create_saved_songs_table():
    """
    Create saved_songs table if not exists, include all necessary info for interacting with spotify api.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS saved_songs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   song_name TEXT NOT NULL,
                   artist_name TEXT NOT NULL,
                   album_name TEXT,
                   song_link TEXT NOT NULL,
                   uri TEXT NOT NULL,
                   user_id INTEGER,
                   FOREIGN KEY (user_id) REFERENCES users(user_id)
               )''')
    conn.commit()
    conn.close()


def save_song(user_id, song_name, artist_name, album_name, song_link, uri):
    """
    Saves a song to current user's MusicMate saved songs.
    """
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO saved_songs (song_name, artist_name, album_name, song_link, uri, user_id)
                     VALUES (?, ?, ?, ?, ?, ?)''', (song_name, artist_name, album_name, song_link, uri, user_id))
        conn.commit()
        song_id = c.lastrowid
        conn.close()
        return song_id
    except sqlite3.IntegrityError as e:
        conn.close()
        return None


def get_saved_songs(user_id):
    """
    Retrieve a user's saved songs, displayed on the saved songs page.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT * FROM saved_songs WHERE user_id=?''', (user_id,))
    saved_songs = c.fetchall()
    conn.close()
    return saved_songs


def delete_saved_song_by_id(user_id, song_id):
    """
    Delete a saved song, needs song's id.
    """
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM saved_songs WHERE id=? AND user_id=?",
                  (song_id, user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting song: {e}")
        conn.close()
        return False


def create_playlists_table():
    """
    Create playlist table with necessary info to interact with Spotify API.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS playlists (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   playlist_id TEXT NOT NULL,
                   playlist_name TEXT NOT NULL,
                   user_id INTEGER,
                   FOREIGN KEY (user_id) REFERENCES users(user_id)
               )''')
    conn.commit()
    conn.close()


# Call this function to create tables if they don't exist yet
if __name__ == "__main__":
    create_saved_songs_table()
