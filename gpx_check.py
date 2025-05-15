import gpxpy

gpx_file = "/home/joetanse/strava_data/activities/138722454.gpx"
try:
    with open(gpx_file, 'r') as file:
        gpx = gpxpy.parse(file)
    print(f"Parsed {gpx_file} successfully")
except Exception as e:
    print(f"Error parsing {gpx_file}: {e}")
