import requests

# === Fill these in ===
SPOTIFY_CLIENT_ID = "your-client-id"
SPOTIFY_CLIENT_SECRET = "your-client-secret"
REFRESH_TOKEN = "your-refresh-token"

def get_access_token():
    print("🔐 Requesting token...")
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        },
    )
    print(f"📡 Response: {response.status_code} - {response.text}")
    response.raise_for_status()
    token = response.json()["access_token"]
    print(f"✅ Access token: {token[:20]}...")  # Print partial token for verification
    return token

if __name__ == "__main__":
    try:
        get_access_token()
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
