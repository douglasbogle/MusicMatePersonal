
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os
from get_spotify_api_key import *
from songs import *
from user_accounts import *
from match_the_day import *
from match_the_song import *
from match_the_mood import *
from decorators import *
from playlist_feature import *
from save_songs import *

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')


@app.route('/')
def home():
    """Render the home page and clear session variables."""
    session.clear()
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle login functionality.

    GET: Render the login page.
    POST: Authenticate the user and redirect to the Spotify info page.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = login_user(username, password)
        if user:
            session['user_id'] = user['user_id']
            return redirect(url_for('get_spotify_info'))
        else:
            flash("Invalid username or password. Please try again.", "danger")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.

    GET: Render the registration page.
    POST: Register a new user and redirect to the login page.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for('register'))

        user_id, error_message = register_user(username, password)
        if user_id is not None:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash(error_message, "danger")
    return render_template('register.html')


@app.route('/get_spotify_info')
def get_spotify_info():
    """
    Redirect to the Spotify authentication URL.
    """
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    """
    Handle Spotify authentication callback.

    Extract authorization code from query parameters and exchange it for an access token.
    """
    if 'error' in request.args:
        return jsonify({'error': request.args['error']})

    if 'code' in request.args:
        token_info = get_token_info(request.args['code'])

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + \
            token_info['expires_in']

        return redirect(url_for('dashboard'))


@app.route('/refresh_token')
def refresh_token_route():
    """
    Route to refresh the Spotify token.
    """
    return refresh_token()


@app.route('/dashboard')
@login_required
@spotify_login_required
def dashboard():
    """
    Render the user dashboard.

    Clears specific session variables and retrieves user data.
    """
    user_id = session['user_id']
    user = get_user_by_id(user_id)

    session.pop('city', None)
    session.pop('activity', None)
    session.pop('genre', None)

    return render_template('dashboard.html', user=user)


@app.route('/match_the_day_info', methods=['GET', 'POST'])
@login_required
@spotify_login_required
def match_the_day_info():
    """
    Handle match the day feature information collection.

    GET: Render the form to collect city, activity, and genre.
    POST: Process form data and render song matches based on activity and weather.
    """
    if request.method == 'POST':
        city = request.form['city']
        activity = request.form['activity']
        genre = request.form['genre']
        session['city'] = city
        session['activity'] = activity
        session['genre'] = genre

        songs, weather_stats = get_songs_from_activity(city, activity, genre)

        if songs is None or weather_stats is None:
            flash("Failed to get song recommendations. Please try again.", "error")
            return redirect(url_for('match_the_day_info'))

        return render_template('song_matches.html', songs=songs, city=city, activity=activity, weather_stats=weather_stats)

    # Reset if navigating back
    session.pop('city', None)
    session.pop('activity', None)
    session.pop('genre', None)
    genres = get_spotify_genres()
    return render_template('match_the_day_info.html', genres=genres)


@app.route('/match_the_mood_info', methods=['GET', 'POST'])
@login_required
@spotify_login_required
def match_the_mood_info():
    """
    Handle match the mood feature information collection.

    GET: Render the form to collect mood and genre.
    POST: Process form data and render song matches based on mood.
    """
    if request.method == 'POST':
        mood = request.form['mood']
        genre = request.form['genre']
        session['mood'] = mood
        session['genre'] = genre

        songs, mood = get_songs_from_mood(mood, genre)

        if not songs:
            flash("No tracks found. Please Try Again!", "error")

        if songs is None:
            flash("Failed to get song recommendations. Please try again.", "error")
            return redirect(url_for('match_the_mood_info'))

        return render_template('song_matches.html', songs=songs, mood=mood)

    # Reset if navigating back
    session.pop('mood', None)
    session.pop('genre', None)
    genres = get_spotify_genres()
    return render_template('match_the_mood_info.html', genres=genres)


@app.route('/match_the_song_info', methods=['GET', 'POST'])
@login_required
@spotify_login_required
def match_the_song_info():
    """
    Handle match the song feature information collection.

    GET: Render the form to collect the original song.
    POST: Process form data and render similar song matches.
    """
    if request.method == 'POST':
        original_song = request.form['song']
        session['original_song'] = original_song

        songs = get_similar_songs(original_song)

        if songs is None:
            flash("Failed to get similar songs. Please try again.", "error")
            return redirect(url_for('match_the_song_info'))

        return render_template('song_matches.html', songs=songs, original_song=original_song)

    # Reset if navigating back
    session.pop('original_song', None)
    genres = get_spotify_genres()
    return render_template('match_the_song_info.html', genres=genres)


@app.route('/song_matches', methods=['GET', 'POST'])
@login_required
@spotify_login_required
def song_matches():
    """
    Render song matches and handle song saving.

    GET: Redirect to the appropriate match feature.
    POST: Save the selected song to the database.
    """
    if request.method == 'POST':
        user_id = session.get('user_id')
        song_name = request.form['song_name']
        artist_name = request.form['artist_name']
        album_name = request.form['album_name']
        song_link = request.form['song_link']
        uri = request.form['uri']

        song_id = save_song(user_id, song_name, artist_name,
                            album_name, song_link, uri)
        if song_id:
            return {"status": "success", "message": "Song saved successfully"}, 200
        else:
            return {"status": "error", "message": "Song failed to save. Please try again"}, 500

    # The following code just grab's the page we came from so that we can redirect the user to it
    previous_page = session.get('previous_page')
    if previous_page == 'match_the_day_info':
        city = session.get('city')
        activity = session.get('activity')
        weather_stats = session.get('weather_stats')
        songs = get_songs_from_activity(city, activity, genre)
        return render_template('song_matches.html', songs=songs, city=city, activity=activity, weather_stats=weather_stats)
    elif previous_page == 'match_the_mood_info':
        mood = session.get('mood')
        genre = session.get('genre')
        songs = get_songs_from_mood(mood, genre)
        return render_template('song_matches.html', songs=songs, mood=mood)
    elif previous_page == 'match_the_song_info':
        original_song = session.get('original_song')
        songs = get_similar_songs(original_song)
        return render_template('song_matches.html', songs=songs, original_song=original_song)


# Route for saving a song
@app.route('/save_a_song', methods=['POST'])
def save_a_song():
    """
    Render the saved songs page and display the user's saved songs and playlists.

    POST: Grab user id and save all the necessary song info to their MusicMate account.
    """
    if request.method == 'POST':
        user_id = session.get('user_id')
        song_name = request.form['song_name']
        artist_name = request.form['artist_name']
        album_name = request.form['album_name']
        song_link = request.form['song_link']
        uri = request.form['uri']

        song_id = save_song(user_id, song_name, artist_name,
                            album_name, song_link, uri)

        if song_id:
            return {"status": "success", "message": "Song saved successfully"}, 200
        else:
            return {"status": "error", "message": "Song failed to save. Please try again"}, 500


# Route for viewing saved songs
@app.route('/saved_songs', methods=['POST', 'GET'])
@login_required
@spotify_login_required
def saved_songs():
    """
    Render the saved songs page and display the user's saved songs and playlists.

    GET/POST: Check for access token and expiration, retrieve saved songs and playlists, and render the page.
    """
    user_id = session.get('user_id')

    if 'access_token' not in session:
        return redirect(url_for('dashboard'))

    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))

    # get saved songs from db
    saved_songs = get_saved_songs(user_id)
    # get playlists from db, should store playlist name and id
    playlists = get_user_playlists()

    return render_template('saved_songs.html', saved_songs=saved_songs, playlists=playlists)


@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    """
    Create a new Spotify playlist with the provided details.

    POST: Validate request JSON, create playlist using the Spotify API, and return success or failure message.
    """
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    data = request.get_json()  # Getting playlist info from popup box
    name = data.get('name')
    description = data.get('description', '')
    public = data.get('public', False)

    # Uses Spotify API to create playlist for user
    response = create_playlist_helper(name, description, public)
    if 'id' in response:
        return jsonify({"success": True, "message": "Playlist created successfully"}), 200
    else:
        return jsonify({"success": False, "message": "Failed to create playlist"}), 500


@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    """
    Add a song to a Spotify playlist.

    POST: Validate request form, add song to playlist using the Spotify API, and redirect to saved songs page.
    """
    if request.method != 'POST':
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    playlist_id = request.form.get('playlist_id')
    song_uri = request.form.get('song_uri')

    result = add_to_playlist_helper(playlist_id, song_uri)
    if result:
        flash("Success.", "yay")
    else:
        flash("Failed.", "danger")

    return redirect(url_for("saved_songs"))


# Route for deleting a saved song
@app.route('/delete_saved_song/<int:song_id>', methods=['POST'])
def delete_saved_song(song_id):
    """
    Delete a saved song from the database.

    POST: Delete the song with the given song_id and redirect to the saved songs page.
    """
    user_id = session.get('user_id')
    if user_id:
        success = delete_saved_song_by_id(user_id, song_id)
        if success:
            flash("Song deleted successfully.", "info")
        else:
            flash("Failed to delete song. Please try again.", "danger")
    else:
        flash("User not found.", "danger")
    return redirect(url_for('saved_songs'))


# Route for logging out
@app.route('/logout')
def logout():
    """
    Log the user out and clear session variables.

    Redirect to the home page.
    """
    session.clear()  # Clear all session variables
    return redirect(url_for('home'))


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
