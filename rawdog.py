# Generate a script that queries InfluxDB directly using requests, bypassing the SDK
raw_patch_script = """
import requests
import csv
import io
print("🐍 Script started.")

# ===== Config =====
SPOTIFY_ACCESS_TOKEN = "BQA0e2DSfKbr1Yjur-rRdfPKMq33Pvahn8osGJVvWmvifsX_2QzMA5phxUnB_IOIUR2gQZP5ojySgXIwNaYIEJWn4n-0TOblV43E1Pklp2gE7QPaTLKPI-8SfbXzzsTUVmbR1nWwbdA5vVDqF855_02Q-6Bjf_2zu-tpEGmj4XeAV5ORplyR3WSy8cRUcU7yBReqyaLmLhjykz-fpyf-NviVDriMmMV81uJiZtA"
INFLUXDB_URL = "http://grafanapi.local:8086"
INFLUXDB_TOKEN = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="
ORG = "grafanapi"
BUCKET = "spotify"

# ===== Raw Flux Query =====
flux_query = '''
from(bucket: "spotify")
  |> range(start: -30d)
  |> filter(fn: (r) =>
    r._measurement == "spotify_play" and
    r.genre == "unknown" and
    r._field == "track"
  )
  |> keep(columns: ["_time", "artist", "track", "album"])
'''

# ===== Execute Raw POST Request =====
headers = {
    "Authorization": f"Token {INFLUXDB_TOKEN}",
    "Content-Type": "application/vnd.flux",
    "Accept": "application/csv"
}

params = {
    "org": ORG
}

print("📡 Sending raw query to Influx...")

print("📡 Attempting HTTP POST to Influx (with timeout)...")
try:
    r = requests.post(
        f"{INFLUXDB_URL}/api/v2/query",
        headers=headers,
        params=params,
        data=flux_query.encode("utf-8"),
        timeout=10
    )
    print(f"✅ Got response: {r.status_code}")
    print(r.text[:500])  # just to preview the body
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    exit(1))

if not r.ok:
    print(f"❌ Query failed: {r.status_code} - {r.text}")
    exit(1)

print("✅ Query succeeded. Parsing CSV...")

csv_content = r.text
reader = csv.DictReader(io.StringIO(csv_content))

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
            "album": album,
            "played_at": played_at
        })

print(f"🔎 Found {len(records)} unknown-tag records.")

for i, rec in enumerate(records):
    print(f"[{i+1}] {rec['artist']} – {rec['track']} ({rec['album']}) @ {rec['played_at']}")
"""
