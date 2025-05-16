import requests
import json
from influxdb_client import InfluxDBClient
import time

# Spotify API Credentials
CLIENT_ID = 'UR TOKEN HERE'
CLIENT_SECRET = 'UR TOKEN HERE'
REDIRECT_URI = 'grafanapi.local'  # The URL to redirect to after authentication

# InfluxDB Credentials
INFLUXDB_URL = 'http://grafanapi.local:8086'
INFLUXDB_TOKEN = '22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=='
INFLUXDB_ORG = 'grafanapi'
INFLUXDB_BUCKET = 'spotify'

# Step 1: Get the access token (OAuth2)
def get_spotify_access_token():
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': 'your_authorization_code',  # This is the code you get after user authentication
        'redirect_uri': REDIRECT_URI
    }

    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers=headers,
        data=data,
        auth=auth
    )

    response_data = response.json()
    return response_data['access_token']

# Step 2: Get Spotify usage data (e.g., top tracks, recently played)
def get_spotify_data(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Example: Get recently played tracks
    response = requests.get(
        'https://api.spotify.com/v1/me/player/recently-played?limit=10',
        headers=headers
    )

    return response.json()

# Step 3: Write data to InfluxDB
def write_to_influxdb(data):
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api()

    for item in data['items']:
        track = item['track']
        json_body = [{
            "measurement": "spotify_usage",
            "tags": {
                "track_name": track['name'],
                "artist_name": track['artists'][0]['name']
            },
            "time": item['played_at'],
            "fields": {
                "play_count": 1,  # We can store the number of plays or use any other field you like
            }
        }]
        write_api.write(bucket=INFLUXDB_BUCKET, record=json_body)

    print("Data written to InfluxDB!")
    client.close()

if __name__ == '__main__':
    # Step 1: Get access token
    access_token = get_spotify_access_token()

    # Step 2: Fetch data from Spotify
    spotify_data = get_spotify_data(access_token)

    # Step 3: Write data to InfluxDB
    write_to_influxdb(spotify_data)
