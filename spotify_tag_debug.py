# Rewriting a debug-enhanced version of the genre fixer that prints results directly
debug_fixer_script = """
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ===== Config =====
SPOTIFY_ACCESS_TOKEN = "BQA0e2DSfKbr1Yjur-rRdfPKMq33Pvahn8osGJVvWmvifsX_2QzMA5phxUnB_IOIUR2gQZP5ojySgXIwNaYIEJWn4n-0TOblV43E1Pklp2gE7QPaTLKPI-8SfbXzzsTUVmbR1nWwbdA5vVDqF855_02Q-6Bjf_2zu-tpEGmj4XeAV5ORplyR3WSy8cRUcU7yBReqyaLmLhjykz-fpyf-NviVDriMmMV81uJiZtA"
INFLUXDB_URL = "http://grafanapi.local:8086"
INFLUXDB_TOKEN = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="
ORG = "grafanapi"
BUCKET = "spotify"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=ORG)
query_api = client.query_api()
write_api = client.write_api(write_options=SYNCHRONOUS)

print("🔍 Running debug Flux query for tag-based 'unknown' genres...")

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) =>
    r._measurement == "spotify_play" and
    r.genre == "unknown" and
    r._field == "track"
  )
  |> keep(columns: ["_time", "artist", "track", "album"])
'''

result = query_api.query(org=ORG, query=query)

print("✅ Query completed.")
print(f"📦 Raw result: {result}")

records = []
for table in result:
    for row in table.records:
        records.append({
            "artist": row.values.get("artist"),
            "track": row.get_value(),
            "album": row.values.get("album"),
            "played_at": row.get_time()
        })

print(f"🔎 Found {len(records)} matching records.")

for i, rec in enumerate(records):
    print(f"[{i+1}] {rec['artist']} – {rec['track']} ({rec['album']}) @ {rec['played_at']}")
"""

# Save this debug-enhanced version

