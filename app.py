from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os
from time import gmtime, strftime  # Import gmtime and strftime
from credentials import CLIENT_ID, CLIENT_SECRET, SECRET_KEY

# Defining consts
TOKEN_CODE = "token_info"
MEDIUM_TERM = "medium_term"
SHORT_TERM = "short_term"
LONG_TERM = "long_term"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("redirectPage", _external=True),
        scope="user-top-read user-library-read"
    )

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = 'Eriks Cookie'

@app.route('/')
def index():
    name = 'username'
    return render_template('index.html', title='Welcome', username=name)

@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirectPage')
def redirectPage():
    print("Redirected URL:", request.url)  # Debugging
    sp_oauth = create_spotify_oauth()

    if "code" not in request.args:
        return "Error: No code returned from Spotify.", 400

    token_info = sp_oauth.get_access_token(request.args["code"])
    print("Token Info:", token_info)  # Print the full response

    session["token_info"] = token_info
    print("Token stored in session:", session.get("token_info"))  # Debugging line

    # Change this line to redirect to getTracks instead of index
    return redirect(url_for('getTracks'))

def get_token():
    token_info = session.get(TOKEN_CODE, None)
    print("Token in session:", token_info)  # Debugging: Check if the token is being retrieved correctly
    if not token_info:
        raise ValueError("No token info found in session.")  # More appropriate exception

    now = int(time.time())
    expires_at = token_info['expires_at']
    print(f"Current time: {now}, Expiry time: {expires_at}")

    is_expired = expires_at - now < 60  # Checking if token expires in less than a minute
    print(f"Is the token expired? {is_expired}")

    if is_expired:
        print("Token is expired, refreshing...")
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        print("Token refreshed:", token_info)
        session["token_info"] = token_info  # Save the refreshed token to session
    
    return token_info

@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except ValueError as e:
        print(f"Error: {str(e)}")
        print("User not logged in")
        return redirect("/")  # Redirect to home if the user is not logged in

    # Proceed to get the top tracks
    sp = spotipy.Spotify(auth=token_info['access_token'])

    try:
        current_user_name = sp.current_user()['display_name']
        short_term = sp.current_user_top_tracks(limit=10, offset=0, time_range=SHORT_TERM)
        medium_term = sp.current_user_top_tracks(limit=10, offset=0, time_range=MEDIUM_TERM)
        long_term = sp.current_user_top_tracks(limit=10, offset=0, time_range=LONG_TERM)
    except Exception as e:
        print(f"Error fetching tracks: {e}")
        return "Error fetching tracks", 500

    if os.path.exists(".cache"): 
        os.remove(".cache")

    return render_template('list.html', user_display_name=current_user_name, short_term=short_term, medium_term=medium_term, long_term=long_term, currentTime=gmtime())

@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    return strftime("%a, %d %b %Y", date)

@app.template_filter('mmss')
def _jinja2_filter_miliseconds(time, fmt=None):
    time = int(time / 1000)
    minutes = time // 60 
    seconds = time % 60 
    if seconds < 10: 
        return str(minutes) + ":0" + str(seconds)
    return str(minutes) + ":" + str(seconds)

if __name__ == "__main__":
    app.run(debug=True)
