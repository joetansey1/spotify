# Full working version of fetch_cron.py, based on your earlier script with the correct indentation and fixed InfluxDB write format

print("🧪 Starting fetch_cron.py...")
import requests
import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ===== InfluxDB Setup =====
TOKEN = "erfvQYLBhrERH9bu8ORZzBRbfQ4GuEM8_f4MYCvVeMJhe38F-K2hZf0C0aNj4MPhk-GyRxufLNRzNrAs0h8gjg=="
ORG = "localorg"
BUCKET = "spotify"
URL = "http://localhost:8086"

client = InfluxDBClient(url=URL, token=TOKEN)
write_api = client.write_api(write_options=SYNCHRONOUS)

# ===== Spotify Setup =====
SPOTIFY_CLIENT_ID = "400ad5deedda48b3b76a1229d54d9791"
SPOTIFY_CLIENT_SECRET = "7f1b6fa6e51848b9963cfaa1aab54af5"
REFRESH_TOKEN = "AQAe0R3NDHJ5TyPuTyTSVahsnqq3dD1sQlQLUL_5CBB0rpOZejoLjYrhd-jqtaIFdUMkE2_TVSiIu2zKeB3sSAn6Q4WRcoG9PJeydeu6QdC63RGqxcUvnZQkiSKTh2Cfq_Q"

def get_access_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]

def fetch_recent_tracks(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "limit": 50
    }
    response = requests.get("https://api.spotify.com/v1/me/player/recently-played", headers=headers, params=params)
    response.raise_for_status()
    return response.json()["items"]

def fetch_artist_genre(artist_id, access_token):
    response = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code != 200:
        return "unknown"
    genres = response.json().get("genres", [])
    return genres[0] if genres else "unknown"

def write_tracks(tracks, access_token):
    for item in tracks:
        track = item["track"]
        artist = track["artists"][0]
        genre = fetch_artist_genre(artist["id"], access_token)

        point = (
            Point("spotify_play")
            .tag("artist", artist["name"])
            .tag("album", track["album"]["name"])
            .tag("genre", genre)
            .tag("track", track["name"])
            .field("duration_ms", track["duration_ms"])
            .field("release_date", track["album"]["release_date"])
            .field("value", 1)
            .time(item["played_at"], WritePrecision.NS)
        )

        print(f"🎵 {item['played_at']} | {artist['name']} – {track['name']} | {genre}")
        try:
            write_api.write(bucket=BUCKET, org=ORG, record=point)
        except Exception as e:
            print(f"⚠️ Failed to write point: {e}")

    write_api.__del__()

# ===== Run the Loop =====
if __name__ == "__main__":
    print("🚀 fetch_cron.py starting up...")

    try:
        print("🔐 Refreshing Spotify access token...")
        access_token = get_access_token()
        print(f"✅ Token acquired: {access_token[:12]}...")

        print("📡 Fetching recent tracks...")
        tracks = fetch_recent_tracks(access_token)
        print(f"🎧 Fetched {len(tracks)} tracks")

        print("📤 Writing tracks to InfluxDB...")
        write_tracks(tracks, access_token)

        print("✅ All done.")
    except Exception as e:
        import traceback
        print("❌ An error occurred:")
        traceback.print_exc()
