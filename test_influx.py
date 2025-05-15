from influxdb_client import InfluxDBClient

# InfluxDB connection parameters
url = "http://localhost:8086"  # Replace with your InfluxDB URL
token = "22wz8ZM3Fq8Vo9IX2ZBuvLaE00BmeHL7Jvzdw41hGoMnRmllyh9qJxyNqSQjtUYpseeJVbstyTWCyX3UoJYT3w=="  # Replace with your actual token
org = "grafanapi"  # Replace with your organization name
bucket = "localbucket"  # Replace with your bucket name

# Initialize InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)

# Query API
query_api = client.query_api()

# Query the data for the last hour (adjust as needed)
query = f'from(bucket: "{bucket}") |> range(start: -1h)'

try:
    # Run the query and fetch the results
    result = query_api.query(query)
    print(f"Query executed successfully. Result: {result}")
except Exception as e:
    print(f"Error executing query: {e}")
finally:
    client.close()
