import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config.secrets import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

class SpotifyHelper:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
        ))

    def play_song(self, query):
        results = self.sp.search(q=query, type="track", limit=1)
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            return "I couldn't find that on Spotify."

        uri = tracks[0]["uri"]
        self.sp.start_playback(uris=[uri])
        return f"Playing: {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}"

    def pause(self):
        self.sp.pause_playback()
        return "⏸️ Paused Spotify."

    def resume(self):
        self.sp.start_playback()
        return "▶️ Resumed Spotify."

    def now_playing(self):
        current = self.sp.currently_playing()
        if not current or not current.get("item"):
            return "I'm not playing anything right now."

        track = current["item"]
        return f"Now playing: {track['name']} by {track['artists'][0]['name']}"
