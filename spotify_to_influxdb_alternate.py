import subprocess
import csv
import io
import json
import urllib.parse
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

print("🔥 ENTERED SCRIPT")

# ===== CONFIG =====
CLIENT_ID = "UR TOKEN HERE SPOTIFY"
CLIENT_SECRET = "UR TOKEN HERE SPOTIFY"
REFRESH_TOKEN = "UR TOKEN HERE SPOTIFY"

INFLUXDB_TOKEN = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="
ORG = "grafanapi"
BUCKET = "spotify"
INFLUX_URL = "http://127.0.0.1:8086"

# ===== Refresh Spotify Access Token =====
def get_access_token():
    auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }
    r = requests.post("https://accounts.spotify.com/api/token", auth=auth_header, data=payload)
    r.raise_for_status()
    return r.json()['access_token']

access_token = get_access_token()
print("🔐 Access token refreshed")

# ===== CURL FLUX QUERY TO FIND UNKNOWN GENRES =====
print("📡 Running curl to Influx...")
flux_query = '''from(bucket: "spotify")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "spotify_play" and r.genre == "unknown" and r._field == "track")
  |> keep(columns: ["_time", "_value", "album", "artist"])'''

r = subprocess.run([
    "curl", "-s", "-X", "POST", f"{INFLUX_URL}/api/v2/query?org={ORG}",
    "-H", f"Authorization: Token {INFLUXDB_TOKEN}",
    "-H", "Content-Type: application/vnd.flux",
    "-H", "Accept: application/csv",
    "--data-binary", flux_query
], stdout=subprocess.PIPE)

csv_data = r.stdout.decode()
print("🔬 CSV Preview:")
print("\n".join(csv_data.strip().split("\n")[0:8]))

reader = csv.DictReader(io.StringIO(csv_data))
records = [row for row in reader if row.get("artist") and row.get("_value")]

print(f"🎯 Found {len(records)} records")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUXDB_TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

for idx, row in enumerate(records, 1):
    artist_name = row["artist"]
    track_name = row["_value"]
    encoded_artist = urllib.parse.quote(artist_name)

    try:
        search_url = f"https://api.spotify.com/v1/search?q={encoded_artist}&type=artist&limit=1"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(search_url, headers=headers)
        resp.raise_for_status()
        artist_info = resp.json()
        print(f"🔎 Spotify response for '{artist_name}':\n{json.dumps(artist_info, indent=2)}")

        items = artist_info["artists"]["items"]
        genres = items[0].get("genres", []) if items else []
        genre = genres[0] if genres else "unknown"
    except Exception as e:
        print(f"⚠️ Failed to fetch genre for '{artist_name}': {e}")
        genre = "unknown"

    print(f"[{idx}/{len(records)}] 🎵 {artist_name} – {track_name} → {genre}")

    point = (
        Point("spotify_play")
        .tag("artist", artist_name)
        .tag("album", row["album"])
        .tag("genre", genre)
        .field("track", track_name)
        .time(row["_time"], WritePrecision.NS)
    )
    write_api.write(bucket=BUCKET, org=ORG, record=point)

print(f"✅ Done. Patched {len(records)} records.")
