# Rewriting with user-provided Spotify access token filled in
full_debug_script = """
import requests
import csv
import io
import time

# ===== Config =====
SPOTIFY_ACCESS_TOKEN = "BQA0e2DSfKbr1Yjur-rRdfPKMq33Pvahn8osGJVvWmvifsX_2QzMA5phxUnB_IOIUR2gQZP5ojySgXIwNaYIEJWn4n-0TOblV43E1Pklp2gE7QPaTLKPI-8SfbXzzsTUVmbR1nWwbdA5vVDqF855_02Q-6Bjf_2zu-tpEGmj4XeAV5ORplyR3WSy8cRUcU7yBReqyaLmLhjykz-fpyf-NviVDriMmMV81uJiZtA"
INFLUXDB_URL = "http://127.0.0.1:8086"
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

headers = {
    "Authorization": f"Token {INFLUXDB_TOKEN}",
    "Content-Type": "application/vnd.flux",
    "Accept": "application/csv"
}

params = {
    "org": ORG
}

print("🐍 Script started.")
print("🧠 Flux being sent:")
print(flux_query)

print("📡 Attempting HTTP POST to Influx with timeout=5s...")
start = time.time()
try:
    r = requests.post(
        f"{INFLUXDB_URL}/api/v2/query",
        headers=headers,
        params=params,
        data=flux_query.encode("utf-8"),
        timeout=5
    )
    duration = time.time() - start
    print(f"✅ Got response in {duration:.2f}s: {r.status_code}")
    print(r.text[:500])
except requests.exceptions.RequestException as e:
    duration = time.time() - start
    print(f"❌ Request failed after {duration:.2f}s: {e}")
"""
