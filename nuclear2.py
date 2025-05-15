# Generate a debug-enhanced version of the dome patcher with loud logging
debug_dome_script = """
import subprocess
import csv
import io
import requests
print("🔥 ENTERED SCRIPT")
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

print("🐍 Script started")

# ===== Config =====
SPOTIFY_ACCESS_TOKEN = "BQA0e2DSfKbr1Yjur-rRdfPKMq33Pvahn8osGJVvWmvifsX_2QzMA5phxUnB_IOIUR2gQZP5ojySgXIwNaYIEJWn4n-0TOblV43E1Pklp2gE7QPaTLKPI-8SfbXzzsTUVmbR1nWwbdA5vVDqF855_02Q-6Bjf_2zu-tpEGmj4XeAV5ORplyR3WSy8cRUcU7yBReqyaLmLhjykz-fpyf-NviVDriMmMV81uJiZtA"
INFLUXDB_TOKEN = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="
ORG = "grafanapi"
BUCKET = "spotify"
INFLUX_URL = "http://127.0.0.1:8086"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUXDB_TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

flux_query = '''
from(bucket: "spotify")
  |> range(start: -30d)
  |> filter(fn: (r) =>
    r._measurement == "spotify_play" and
    r.genre == "unknown" and
    r._field == "track"
  )
  |> keep(columns: ["_time", "artist", "track", "album"])
'''.strip()

print("📡 Running curl to Influx...")

result = subprocess.run([
    "curl", "-s",
    "-X", "POST", f"{INFLUX_URL}/api/v2/query?org={ORG}",
    "-H", f"Authorization: Token {INFLUXDB_TOKEN}",
    "-H", "Content-Type: application/vnd.flux",
    "-H", "Accept: application/csv",
    "--data-binary", flux_query
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if result.returncode != 0:
    print("❌ Curl failed:")
    print(result.stderr.decode())
    exit(1)

csv_data = result.stdout.decode()
print("🔬 CSV preview:")
print(csv_data[:500])

reader = csv.DictReader(io.StringIO(csv_data))
records = []

for row in reader:
    artist = row.get("artist")
    track = row.get("_value")
    album = row.get("album")
    played_at = row.get("_time")
    if artist and track and played_at:
        records.append({
            "artist": artist,
            "track": track,
            "album": album or "unknown",
            "played_at": played_at
        })

print(f"🎯 Found {len(records)} records")

def get_artist_genre(artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"}
    params = {"q": artist_name, "type": "artist", "limit": 1}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        r.raise_for_status()
        items = r.json().get("artists", {}).get("items", [])
        if items:
            artist_id = items[0]["id"]
            genre_url = f"https://api.spotify.com/v1/artists/{artist_id}"
            genre_r = requests.get(genre_url, headers=headers, timeout=5)
            genre_r.raise_for_status()
            genres = genre_r.json().get("genres", [])
            return genres[0] if genres else "unknown"
    except Exception as e:
        print(f"⚠️ Failed genre for '{artist_name}': {e}")
    return "unknown"

patched = 0
for i, rec in enumerate(records):
    genre = get_artist_genre(rec["artist"])
    print(f"[{i+1}/{len(records)}] 🎵 {rec['artist']} – {rec['track']} → {genre}")
    point = (
        Point("spotify_play")
        .tag("artist", rec["artist"])
        .tag("album", rec["album"])
        .field("track", rec["track"])
        .field("genre", genre)
        .time(rec["played_at"], WritePrecision.NS)
    )
    try:
        write_api.write(bucket=BUCKET, org=ORG, record=point)
        patched += 1
    except Exception as e:
        print(f"❌ Failed to write: {e}")

print(f"✅ Done. Patched {patched} records.")
"""

