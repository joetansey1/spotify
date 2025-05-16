
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ======== Config =========
SPOTIFY_ACCESS_TOKEN = "UR TOKEN HERE"
INFLUXDB_URL = 'http://grafanapi.local:8086'
INFLUXDB_TOKEN = '22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=='
ORG = "grafanapi"
BUCKET = "spotify"

# ======== Setup InfluxDB client =========
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

import time

def fetch_artist_genre(artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        genres = r.json().get("genres", [])
        return genres[0] if genres else "unknown"
    except Exception as e:
        print(f"⚠️ Failed to fetch genre for artist {artist_id}: {e}")
        return "unknown"
    finally:
        time.sleep(0.1)  # light throttle



def fetch_recent_tracks():
    url = 'https://api.spotify.com/v1/me/player/recently-played?limit=50'
    headers = {'Authorization': f'Bearer {SPOTIFY_ACCESS_TOKEN}'}
    all_tracks = []

    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        all_tracks.extend(data['items'])
        url = data.get('next')

    return all_tracks

def write_tracks(tracks):
    for item in tracks:
        played_at = item['played_at']
        track = item['track']
        track_name = track['name']
        artist = track['artists'][0]['name']
        artist_id = track['artists'][0]['id']
        album = track['album']['name']
        release_date = track['album'].get('release_date', 'unknown')
        duration_ms = track.get('duration_ms', 0)
        genre = fetch_artist_genre(artist_id)

        print(f"🎵 Writing: {played_at} | {artist} – {track_name} | {genre}")

        point = Point("spotify_play") \
            .tag("artist", artist) \
            .tag("album", album) \
            .tag("genre", genre) \
            .field("track", track_name) \
            .field("release_date", release_date) \
            .field("duration_ms", duration_ms) \
            .time(played_at, WritePrecision.NS)

        try:
            write_api.write(bucket=BUCKET, org=ORG, record=point)
        except Exception as e:
            print(f"⚠️ Write failed: {e}")

if __name__ == "__main__":
    print(f"📡 Writing to bucket='{BUCKET}' in org='{ORG}' at '{INFLUXDB_URL}'")
    tracks = fetch_recent_tracks()
    print(f"✅ Fetched {len(tracks)} tracks")
    write_tracks(tracks)
    write_api.flush()
    client.close()
    print("✅ Done writing to InfluxDB")
