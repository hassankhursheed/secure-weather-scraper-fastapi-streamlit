import json
import csv
from datetime import datetime

# filename generator
def generate_filename(data, extension):
    now = datetime.now()

    city = data.get("City", "unknown").lower().replace(" ", "_")
    date_time = now.strftime("%d_%m_%Y_%H_%M_%S")

    return f"{city}_{date_time}.{extension}"


# save as json
def save_to_json(data):
    filename = generate_filename(data, "json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return filename


# save as csv
def save_to_csv(data):
    filename = generate_filename(data, "csv")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])

        for key, value in data.items():
            writer.writerow([key, value])

    return filename
