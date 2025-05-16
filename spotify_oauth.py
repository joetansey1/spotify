import http.server
import socketserver
import urllib.parse
import webbrowser
import requests

# Replace with your Spotify app credentials
CLIENT_ID = 'UR TOKEN'
CLIENT_SECRET = 'UR TOKEN'
REDIRECT_URI = 'https://grafanapi.local/callback'  # The URL to redirect to after authentication

# Authorization URL for Spotify
auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&scope=user-library-read"

# Set up a simple HTTP server to capture the auth code
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/callback"):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            code = params.get("code", [None])[0]

            if code:
                print(f"Authorization code received: {code}")
                self.exchange_code_for_token(code)
            else:
                print("No authorization code found in the response.")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization complete. You can close this window.")

    def exchange_code_for_token(self, code):
        """Exchanges the authorization code for an access token"""
        token_url = "https://accounts.spotify.com/api/token"
        auth = (CLIENT_ID, CLIENT_SECRET)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        response = requests.post(token_url, headers=headers, data=data, auth=auth)
        response_data = response.json()

        if "access_token" in response_data:
            print(f"Access Token: {response_data['access_token']}")
        else:
            print("Error retrieving access token.")

def run_server():
    PORT = 8080
    handler = MyHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    print("Serving at port", PORT)
   # webbrowser.open(auth_url)
    import os
    os.system(f"xdg-open {auth_url}") 
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
