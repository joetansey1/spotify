# Script that uses subprocess to call curl for InfluxDB Flux query, parses the CSV, and prints the records
import subprocess

curl_patch_script = """
import subprocess
import csv
import io

# ===== Config =====
SPOTIFY_ACCESS_TOKEN = "BQA0e2DSfKbr1Yjur-rRdfPKMq33Pvahn8osGJVvWmvifsX_2QzMA5phxUnB_IOIUR2gQZP5ojySgXIwNaYIEJWn4n-0TOblV43E1Pklp2gE7QPaTLKPI-8SfbXzzsTUVmbR1nWwbdA5vVDqF855_02Q-6Bjf_2zu-tpEGmj4XeAV5ORplyR3WSy8cRUcU7yBReqyaLmLhjykz-fpyf-NviVDriMmMV81uJiZtA"
INFLUXDB_TOKEN = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="
ORG = "grafanapi"
BUCKET = "spotify"
INFLUX_URL = "http://127.0.0.1:8086"

# ===== Flux Query =====
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

print("📡 Calling Influx via curl...")

result = subprocess.run([
    "curl", "-s",
    "-X", "POST", f"{INFLUX_URL}/api/v2/query?org={ORG}",
    "-H", f"Authorization: Token {INFLUXDB_TOKEN}",
    "-H", "Content-Type: application/vnd.flux",
    "-H", "Accept: application/csv",
    "--data-binary", flux_query
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if result.returncode != 0:
    print("❌ curl failed:")
    print(result.stderr.decode())
    exit(1)

csv_data = result.stdout.decode()

if not csv_data.strip():
    print("🕳️ No data returned.")
    exit(0)

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
            "album": album,
            "played_at": played_at
        })

print(f"🎯 Parsed {len(records)} records from Influx via curl.")
for i, rec in enumerate(records):
    print(f"[{i+1}] {rec['artist']} – {rec['track']} ({rec['album']}) @ {rec['played_at']}")
"""
