# Generate a genre repair script to patch "unknown" genres in InfluxDB
repair_script = """
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ===== Config =====
SPOTIFY_ACCESS_TOKEN = "BQDsNx8_m5f4pu0C0pji0ccTb6fET8tc5qiRVmFa6YtuzRpT9bTQ4KV2FDNS8N9tI20Ty5_FDgeyIaMwIsevr52iiDxcqTrUSuldV8aijoo54hWgcSuTqZyFF4_hoxp3S2qJ7iRisVp16K2eU6p5E7PW6cO0x6IhViBptedvTcKvn9lGJ9ePKIqbdosNrWvveQAZoJGWl1men1aZNR-2GYozew7xo_Z72uYuOO4"
INFLUXDB_URL = "http://grafanapi.local:8086"
INFLUXDB_TOKEN = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="
ORG = "grafanapi"
BUCKET = "spotify"

# ===== Influx Setup =====
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=ORG)
query_api = client.query_api()
write_api = client.write_api(write_options=SYNCHRONOUS)

print("🔍 Querying unknown genres...")
query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "spotify_play" and r["genre"] == "unknown")
  |> keep(columns: ["_time", "artist", "track", "album"])
'''

result = query_api.query(org=ORG, query=query)

print("✅ Query complete. Parsing results...")

records = []
for table in result:
    for row in table.records:
        records.append({
            "artist": row.values.get("artist"),
            "track": row.values.get("track"),
            "album": row.values.get("album"),
            "played_at": row.get_time()
        })

print(f"🔢 Found {len(records)} 'unknown' records to patch.")


records = []
for table in result:
    for row in table.records:
        records.append({
            "artist": row.values.get("artist"),
            "track": row.values.get("track"),
            "album": row.values.get("album"),
            "played_at": row.get_time()
        })

def get_artist_id(artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"}
    params = {"q": artist_name, "type": "artist", "limit": 1}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        r.raise_for_status()
        items = r.json().get("artists", {}).get("items", [])
        return items[0]["id"] if items else None
    except Exception as e:
        print(f"⚠️ Failed to fetch artist ID for '{artist_name}': {e}")
        return None

def get_primary_genre(artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        genres = r.json().get("genres", [])
        return genres[0] if genres else "unknown"
    except Exception as e:
        print(f"⚠️ Failed to fetch genre for ID {artist_id}: {e}")
        return "unknown"

print(f"🔁 Attempting to patch {len(records)} records...\n")

patched = 0
for rec in records:
    artist = rec["artist"]
    track = rec["track"]
    album = rec["album"]
    played_at = rec["played_at"]

    if not artist or not track or not played_at:
        continue

    artist_id = get_artist_id(artist)
    if not artist_id:
        continue

    genre = get_primary_genre(artist_id)
    print(f"🎵 {artist} – {track} @ {played_at} → {genre}")

    point = Point("spotify_play") \\
        .tag("artist", artist) \\
        .tag("album", album or "unknown") \\
        .tag("genre", genre) \\
        .field("track", track) \\
        .time(played_at, WritePrecision.NS)

    try:
        write_api.write(bucket=BUCKET, org=ORG, record=point)
        patched += 1
    except Exception as e:
        print(f"⚠️ Write failed for {artist}: {e}")

client.close()
print(f"✅ Patched {patched} records.")
"""

# Save the script
