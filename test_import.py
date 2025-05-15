import logging
import gzip
import fitparse
from influxdb_client import InfluxDBClient
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[
    logging.StreamHandler(),  # Print to console
    logging.FileHandler("/home/joetanse/strava_to_influx.log")  # Save to file
])

# InfluxDB 2.x connection parameters
url = "http://grafanapi.local:8086"  # InfluxDB URL with correct domain
token = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="  # Use the token you provided
org = "grafanapi"  # Replace with your organization name
bucket = "localbucket"  # Replace with your bucket name

# Initialize InfluxDB client with token authentication
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

# Path to the .fit.gz file you want to import
fit_gz_file_path = os.path.expanduser("/home/joetanse/strava_data/activities/999542782.fit.gz")  # Ensure correct path

# Function to process the .fit.gz file and insert one record into InfluxDB
def process_fit_file(file_path):
    try:
        # Decompress the .fit.gz file
        with gzip.open(file_path, 'rb') as f:
            fit_file = fitparse.FitFile(f)

            # Loop through the records in the .fit file and get data points
            for record in fit_file.get_messages("record"):
                timestamp = record.get_value("timestamp").isoformat()
                latitude = record.get_value("position_lat")
                longitude = record.get_value("position_long")
                elevation = record.get_value("altitude")

                # Log each point to check if we have all the data
                logging.info(f"Processing point - Timestamp: {timestamp}, Lat: {latitude}, Lon: {longitude}, Elev: {elevation}")

                # Prepare data for InfluxDB
                json_body = [{
                    "measurement": "strava_fit_activity",
                    "tags": {
                        "activity_type": "fit",
                        "file_name": file_path
                    },
                    "time": timestamp,
                    "fields": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "elevation": elevation
                    }
                }]
                # Write the record to InfluxDB
                write_api.write(bucket=bucket, record=json_body)
                logging.info(f"Data point written: {timestamp}, Lat: {latitude}, Lon: {longitude}, Elev: {elevation}")

    except Exception as e:
        logging.error(f"Error processing FIT file {file_path}: {e}")

# Call the function to process the file and import one record
process_fit_file(fit_gz_file_path)

# Close the client connection
client.close()

logging.info("Data successfully imported into InfluxDB!")
