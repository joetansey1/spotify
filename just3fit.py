import csv
import fitparse
import os

# Path to the directory containing the .fit files
file_directory = '/home/joetanse/strava_data/activities/'

# List to store the first 3 .fit files
file_paths = []

# Loop through the files in the directory and grab the first 3 .fit files
for filename in os.listdir(file_directory):
    if filename.endswith(".fit"):
        file_paths.append(os.path.join(file_directory, filename))
    if len(file_paths) >= 3:  # Stop after collecting 3 files
        break

# Check if we found 3 files
if len(file_paths) < 3:
    print("Not enough .fit files found.")
else:
    # Open the CSV file once
    with open('subset_extracted_fit_data.csv', mode='w', newline='') as csvfile:
        fieldnames = ['file_name', 'timestamp', 'latitude', 'longitude', 'elevation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()  # Write the header once at the beginning

        # Loop through each of the first 3 file paths
        for file_path in file_paths:
            try:
                fit_file = fitparse.FitFile(file_path)

                # Loop through the records in the FIT file
                for record in fit_file.get_messages("record"):
                    timestamp = record.get_value("timestamp").isoformat()
                    latitude = record.get_value("position_lat")
                    longitude = record.get_value("position_long")
                    elevation = record.get_value("altitude")

                    # Skip records with missing data
                    if latitude is None or longitude is None or elevation is None:
                        continue

                    # Write to CSV
                    writer.writerow({
                        'file_name': file_path,
                        'timestamp': timestamp,
                        'latitude': latitude,
                        'longitude': longitude,
                        'elevation': elevation
                    })
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    print("Subset data exported to subset_extracted_fit_data.csv")
