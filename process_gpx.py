import gpxpy
import logging
import os
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Timeout handler for GPX parsing (60 seconds)
def handler(signum, frame):
    raise Exception("Timeout: GPX parsing took too long.")

# Timeout for writing to InfluxDB (60 seconds)
def write_to_influxdb_with_timeout(data_batch):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(write_to_influxdb, data_batch)
        try:
            future.result(timeout=60)  # Set timeout to 60 seconds
        except TimeoutError:
            logging.error(f"Timeout when writing {len(data_batch)} records to InfluxDB")
            return False
    return True

# Initialize global variables
BATCH_SIZE = 5  # Set the batch size (adjust as needed)
data_batch = []
timestamps_batch = []  # Initialize timestamps_batch
processed_timestamps = set()

# Automatically use the directory '~/strava_data/activities'
GPX_FOLDER = os.path.expanduser("~/strava_data/activities")

# Function to check duplicates by timestamp (you can adjust this as needed)
def check_duplicates_in_batch(timestamps_batch):
    return any(timestamp in processed_timestamps for timestamp in timestamps_batch)

# Function to write data to InfluxDB (you can adjust this for your setup)
def write_to_influxdb(data_batch):
    # Replace this with your code to write `data_batch` to InfluxDB
    pass

# Function to process a single GPX file
def process_gpx(gpx_file, data_batch):
    global timestamps_batch  # Ensure we are modifying the global timestamps_batch

    logging.info(f"Starting to process file: {gpx_file}")

    # Set timeout for the file parsing process (60 seconds)
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(60)

    try:
        with open(gpx_file, 'r') as file:
            logging.info(f"Parsing {gpx_file}...")
            gpx = gpxpy.parse(file)
            logging.info(f"Successfully parsed {gpx_file}")
            logging.info(f"Number of tracks: {len(gpx.tracks)}")
            logging.info(f"Number of segments: {len(gpx.tracks[0].segments)}")
            logging.info(f"Number of points: {len(gpx.tracks[0].segments[0].points)}")

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        timestamp = point.time.isoformat()
                        timestamps_batch.append(timestamp)
                        if len(timestamps_batch) >= BATCH_SIZE:  # Once we reach a batch size
                            if check_duplicates_in_batch(timestamps_batch):
                                logging.debug(f"Skipping batch of {len(timestamps_batch)} records in {gpx_file} due to duplicates.")
                                timestamps_batch = []  # Clear the batch
                                continue

                        # Add to data_batch for writing
                        json_body = [{
                            "measurement": "strava_gpx_activity",
                            "tags": {
                                "activity_type": "gpx",
                                "file_name": gpx_file
                            },
                            "time": timestamp,
                            "fields": {
                                "latitude": point.latitude,
                                "longitude": point.longitude,
                                "elevation": point.elevation
                            }
                        }]
                        data_batch.extend(json_body)

            # After processing the file, if there are any remaining timestamps, check them
            if timestamps_batch:
                if check_duplicates_in_batch(timestamps_batch):
                    logging.debug(f"Skipping batch of {len(timestamps_batch)} records in {gpx_file} due to duplicates.")
                timestamps_batch = []  # Reset batch

    except Exception as e:
        logging.error(f"Error processing file {gpx_file}: {e}")
        return  # Skip this file and continue with the next one

# Main processing loop for files in the folder
def process_files_in_folder(folder_path):
    global processed_timestamps, timestamps_batch  # Access the global variables
    data_batch = []  # Initialize data_batch here to prevent UnboundLocalError

    # List all files in the directory
    for gpx_file in os.listdir(folder_path):
        if gpx_file.endswith(".gpx"):
            gpx_file_path = os.path.join(folder_path, gpx_file)
            logging.info(f"Processing file: {gpx_file_path}")
            process_gpx(gpx_file_path, data_batch)

            if data_batch:
                # Write data with timeout handling
                write_to_influxdb_with_timeout(data_batch)
                data_batch = []  # Clear the batch after writing

            # Add the new timestamps to the set
            processed_timestamps.update(timestamps_batch)
            timestamps_batch = []  # Reset batch for next file

# Process all GPX files in the specified folder
process_files_in_folder(GPX_FOLDER)
