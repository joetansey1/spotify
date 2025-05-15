from influxdb_client import InfluxDBClient
import csv
import time

# InfluxDB connection parameters
url = "http://grafanapi.local:8086"  # Updated InfluxDB URL
token = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="  # Replace with your actual token
org = "grafanapi"  # Replace with your organization name
bucket = "localbucket"  # Replace with your bucket name

# Initialize InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

# Path to your CSV file
csv_file_path = '/home/joetanse/subset_extracted_fit_data.csv'

# Open the CSV file and read the data
with open(csv_file_path, mode='r') as csvfile:
    reader = csv.DictReader(csvfile)
    
    # Iterate over each row in the CSV file
    for row in reader:
        timestamp = row['timestamp']
        latitude = float(row['latitude'])
        longitude = float(row['longitude'])
        elevation = float(row['elevation'])
        
        # Prepare data point for InfluxDB
        json_body = [{
            "measurement": "strava_fit_activity",
            "tags": {
                "file_name": row['file_name']
            },
            "time": timestamp,
            "fields": {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation
            }
        }]
        
        # Write data to InfluxDB
        write_api.write(bucket=bucket, record=json_body)

        # Optional: print a message for every 1000 records written (for monitoring)
        if int(reader.line_num) % 1000 == 0:
            print(f"Written {reader.line_num} records to InfluxDB.")

# Close the client connection after writing all data
client.close()
print("All data successfully written to InfluxDB!")
