import sqlite3
from datetime import datetime

DB_NAME = "weather.db"


# Create weather table
def create_table():
    # Create database connection
    create_connection = sqlite3.connect(DB_NAME)
    # Create cursor object, usen to run SQL queries
    cursor = create_connection.cursor()

    # here, it will Create "weather_data" table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            country TEXT,
            temperature REAL,
            feels_like REAL,
            min_temp REAL,
            max_temp REAL,
            humidity INTEGER,
            weather TEXT,
            wind_speed REAL,
            pressure INTEGER,
            visibility INTEGER,
            latitude REAL,
            longitude REAL,
            fetched_at TEXT
        )
    """)
    # commit changes and close connection
    create_connection.commit()
    create_connection.close()

# Insert fetched weather data into database
def insert_weather_data(data: dict):
    create_connection = sqlite3.connect(DB_NAME)
    cursor = create_connection.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Insert data into weather_data table
    cursor.execute("""
        INSERT INTO weather_data (
            city, country, temperature, feels_like,
            min_temp, max_temp, humidity, weather,
            wind_speed, pressure, visibility,
            latitude, longitude, fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["City"],
        data["Country Code"],
        float(data["Temperature"].split()[0]),
        float(data["Feels Like"].split()[0]),
        float(data["Min Temperature"].split()[0]),
        float(data["Max Temperature"].split()[0]),
        int(data["Humidity"].replace("%", "")),
        data["Weather"],
        float(data["Wind Speed"].split()[0]),
        int(data["Pressure"].split()[0]),
        int(data["Visibility"].split()[0]) if data["Visibility"] != "N/A meters" else None,
        data["Latitude"],
        data["Longitude"],
        datetime.utcnow().isoformat()
    ))
    # commit changes and close connection
    create_connection.commit()
    create_connection.close()