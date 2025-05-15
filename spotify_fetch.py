import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ======== Config =========
SPOTIFY_ACCESS_TOKEN = "BQBUYRawIP-mqSg21kxw4EiwYUrkOKVrhfvGtHvHhC6BAFgeRVYBIELkY_CQL9PE-VWofucWewLa8s89pbImXKVk6Gyibp-AVpaUj_BxAuB3EpxIqSKqrI_oaSXopQTBcDIvoqpi-xTbd9xWwQvz4Dn30e8OasgyKzpFQuLlH36UMWIzpRbUenlUALgt4SXpvopBBTFFGum7jXsmV5UtwP0EzxlT7ysnWelc9PM"
INFLUXDB_URL = 'http://grafanapi.local:8086'
INFLUXDB_TOKEN = '22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=='
ORG = "grafanapi"
BUCKET = "spotify"

print(f"📡 Writing to bucket='{BUCKET}' in org='{ORG}' at '{INFLUXDB_URL}'")

# ======== Influx Client Setup =========
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# ======== Spotify Fetch Logic =========
def fetch_all_recent_tracks():
    url = 'https://api.spotify.com/v1/me/player/recently-played?limit=50'
    headers = {'Authorization': f'Bearer {SPOTIFY_ACCESS_TOKEN}'}
    all_tracks = []

    while url:
        print(f"Fetching: {url}")
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        all_tracks.extend(data['items'])
        url = data.get('next')

    return all_tracks

# ======== InfluxDB Writer =========
def write_tracks_to_influx(tracks):
    for item in tracks:
        track = item['track']
        played_at = item['played_at']
        artist = track['artists'][0]['name']
        album = track['album']['name']
        song = track['name']

        print(f"🎵 Writing: {played_at} | {artist} – {song}")

        point = Point("spotify_play") \
            .tag("artist", artist) \
            .tag("album", album) \
            .field("track", song) \
            .time(played_at, WritePrecision.NS)

        try:
            write_api.write(bucket=BUCKET, org=ORG, record=point)
        except Exception as e:
            print(f"⚠️ Write failed: {e}")

# ======== Run It =========
if __name__ == "__main__":
    tracks = fetch_all_recent_tracks()
    print(f"✅ Fetched {len(tracks)} total tracks")
    write_tracks_to_influx(tracks)
    write_api.flush()
    client.close()
    print("✅ Done writing to InfluxDB")
