import requests
from bs4 import BeautifulSoup
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sys

def create_spotify_playlist(date):
    # Fetch Spotify API credentials from environment variables
    CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
    REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')

    # Check if Spotify API credentials are available
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        return None  # Handle this case appropriately in your Flask route

    # Your code for fetching song names from Billboard
    URL_BASE = "https://www.billboard.com/charts/hot-100/"
    URL = URL_BASE + date

    response = requests.get(URL)
    if response.status_code != 200:
        return None  # Handle this case appropriately in your Flask route

    website = response.text
    soup = BeautifulSoup(website, "html.parser")

    all_songs = soup.select("li ul li h3")
    song_names = [song.getText().strip() for song in all_songs]

    # Initialize Spotify API
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope="playlist-modify-private"))

    # Create a new playlist with the inputted date in the name
    playlist_name = f"Billboard Hot 100 - {date}"
    playlist_description = "Top songs from Billboard Hot 100"
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user_id, playlist_name, public=False, description=playlist_description)

    # Add songs to the playlist
    for song_name in song_names:
        result = sp.search(song_name, limit=1)
        if result["tracks"]["items"]:
            track_uri = result["tracks"]["items"][0]["uri"]
            sp.playlist_add_items(playlist["id"], [track_uri])

    return playlist["external_urls"]["spotify"]
