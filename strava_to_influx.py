import logging
import gpxpy
import os
import pytcx
import fitparse
from influxdb_client import InfluxDBClient
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[
    logging.StreamHandler(),  # Print to console
    logging.FileHandler("/home/joetanse/strava_to_influx.log")  # Save to file
])

# InfluxDB 2.x connection parameters
url = "http://localhost:8086"  # Replace with your InfluxDB URL
token = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="  # Replace with your actual token
org = "grafanapi"  # Replace with your organization name
bucket = "localbucket"  # Replace with your bucket name

# Initialize InfluxDB client with token authentication
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

# Path to the directory containing the GPX, TCX, and FIT files
file_directory = "/home/joetanse/strava_data/activities/"  # Adjust the path accordingly

# Define the batch size
BATCH_SIZE = 5  # You can adjust this based on your system's capabilities

# File to skip manually
skip_file = "/home/joetanse/strava_data/activities/138722454.gpx"

# Function to write data in batches
def write_batch(data_points):
    if data_points:
        write_api.write(bucket=bucket, record=data_points)

def check_duplicate(file_name, timestamp):
    query = f"""
    from(bucket: "{bucket}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "strava_gpx_activity" and r["file_name"] == "{file_name}" and r["time"] == "{timestamp}")
    """
    try:
        result = client.query_api().query(query)
        return len(result) > 0
    except Exception as e:
        logging.error(f"Error checking duplicate for {file_name} at {timestamp}: {e}")
        return False

# Accumulate data points in a list
data_batch = []

def process_file(file_path, file_type):
    global data_batch
    try:
        if file_type == "gpx":
            with open(file_path, 'r') as file:
                gpx = gpxpy.parse(file)
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            timestamp = point.time.isoformat()
                            if check_duplicate(file_path, timestamp):
                                continue
                            json_body = [{
                                "measurement": "strava_gpx_activity",
                                "tags": {
                                    "activity_type": "gpx",
                                    "file_name": file_path
                                },
                                "time": timestamp,
                                "fields": {
                                    "latitude": point.latitude,
                                    "longitude": point.longitude,
                                    "elevation": point.elevation
                                }
                            }]
                            data_batch.extend(json_body)

        elif file_type == "tcx":
            with open(file_path, 'r') as file:
                tcx = pytcx.parse(file)
                for activity in tcx.activities:
                    for track in activity.tracks:
                        for point in track.points:
                            timestamp = point.timestamp.isoformat()
                            if check_duplicate(file_path, timestamp):
                                continue
                            json_body = [{
                                "measurement": "strava_tcx_activity",
                                "tags": {
                                    "activity_type": "tcx",
                                    "file_name": file_path
                                },
                                "time": timestamp,
                                "fields": {
                                    "latitude": point.latitude,
                                    "longitude": point.longitude,
                                    "elevation": point.elevation
                                }
                            }]
                            data_batch.extend(json_body)

        elif file_type == "fit":
            fit_parser = fitparse.FitFile(file_path)
            for record in fit_parser.get_messages("record"):
                timestamp = record.get_value("timestamp").isoformat()
                if check_duplicate(file_path, timestamp):
                    continue
                json_body = [{
                    "measurement": "strava_fit_activity",
                    "tags": {
                        "activity_type": "fit",
                        "file_name": file_path
                    },
                    "time": timestamp,
                    "fields": {
                        "latitude": record.get_value("position_lat"),
                        "longitude": record.get_value("position_long"),
                        "elevation": record.get_value("altitude")
                    }
                }]
                data_batch.extend(json_body)

        # Write the batch if it reaches the specified size
        if len(data_batch) >= BATCH_SIZE:
            write_batch(data_batch)
            data_batch = []  # Reset the batch
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")

# Function to handle retries for writing to InfluxDB
def write_with_retry(data_batch, retries=3, delay=5):
    for attempt in range(retries):
        try:
            write_batch(data_batch)
            return True
        except TimeoutError:
            logging.error(f"Timeout error writing batch. Retry {attempt+1} of {retries}.")
            time.sleep(delay)
        except Exception as e:
            logging.error(f"Error writing batch: {e}")
            return False
    return False

# Loop through all files in the directory and process them sequentially
for filename in os.listdir(file_directory):
    file_path = os.path.join(file_directory, filename)

    # Check if this is the file we want to skip
    if file_path == skip_file:
        logging.warning(f"Skipping file {file_path} manually.")
        continue  # Skip this file

    # Log the current file being processed
    logging.info(f"Processing file: {filename}")

    if filename.endswith(".gpx"):
        process_file(file_path, "gpx")
    elif filename.endswith(".tcx"):
        process_file(file_path, "tcx")
    elif filename.endswith(".fit"):
        process_file(file_path, "fit")

    logging.info(f"Finished processing: {filename}")

# Write any remaining data points in the batch
write_with_retry(data_batch)

# Close the client connection after all writes
client.close()

logging.info("All data successfully imported into InfluxDB!")
