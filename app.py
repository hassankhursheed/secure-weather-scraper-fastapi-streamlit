from datetime import datetime
import streamlit as st
from weather_api import fetch_weather
from utils import save_to_json, save_to_csv
import pandas as pd
from database import create_table, insert_weather_data
import os
import hmac
import hashlib
import secrets
import time
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("STREAMLIT_USERNAME")
PASSWORD = os.getenv("STREAMLIT_PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("Streamlit credentials not set in .env")


# login token settings, used to keep the user logged in across page refresh
TOKEN_TTL_SECONDS = 8 * 60 * 60  # 8 hours


# random signing key, created once per server start (a new key logs everyone out)
@st.cache_resource
def get_signing_key():
    return secrets.token_bytes(32)


# create a signed login token that expires after TOKEN_TTL_SECONDS
def create_login_token():
    expires = str(int(time.time()) + TOKEN_TTL_SECONDS)
    signature = hmac.new(get_signing_key(), f"{USERNAME}:{expires}".encode(), hashlib.sha256).hexdigest()
    return f"{expires}.{signature}"


# check that a login token was signed by this server and has not expired
def is_valid_login_token(token):
    try:
        expires, signature = token.split(".")
        expected = hmac.new(get_signing_key(), f"{USERNAME}:{expires}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected) and int(expires) > time.time()
    except (AttributeError, ValueError):
        return False


st.set_page_config(page_title="Weather App", layout="centered")

# Initialize database
create_table()


# Session state management

# query params for persistent login state across refresh 
query_params = st.query_params
# Session state for login
if "logged_in" not in st.session_state:
    # Check if user was logged in (signed, unexpired token in the URL)
    st.session_state.logged_in = is_valid_login_token(query_params.get("auth"))
# Session state for weather page
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None


# UI functions

# UI for login page
def login_ui():
    st.title("Login to Weather App")
    st.markdown("Please enter your credentials to access the weather data extractor.")
    # Login form
    with st.form("login_form"):
        user = st.text_input("Username", placeholder="Enter username")
        pwd = st.text_input("Password", type="password", placeholder="Enter password")
        login_clicked = st.form_submit_button("Login", use_container_width=True, type="primary")

        if login_clicked:
            if user == USERNAME and pwd == PASSWORD:
                st.session_state.logged_in = True
                
                # Add a signed login token to the URL to persist across refresh
                st.query_params["auth"] = create_login_token()
                
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid username or password")

# UI for weather page
def weather_ui():
    # sidebar
    with st.sidebar:
        st.title("User Profile")
        st.write(f"**Username:** {USERNAME}")
        st.write("**Role:** User")
        st.write("**App:** Weather Data Extractor")
        st.divider()
        # Logout button
        if st.button("Logout", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.weather_data = None
            
            # Remove auth from URL and change the signing key so old tokens stop working
            if "auth" in st.query_params:
                del st.query_params["auth"]
            get_signing_key.clear()
            
            st.rerun()

    # Main page content
    st.title("Weather Data Extractor")
    st.markdown("##### Enter details below to fetch real-time weather data.")

    # Weather form
    with st.form("weather_form"):
        col1, col2 = st.columns([3, 1])
        
        # Inputs for city and unit
        with col1:
            city = st.text_input("Enter City Name", placeholder="e.g., Lahore, New York, etc.")
        
        with col2:
            unit = st.selectbox("Select Units", ["metric", "imperial"], help="metric = Celsius\n\nimperial = Fahrenheit")
        
        # Fetch button
        fetch_clicked = st.form_submit_button("Fetch Weather", use_container_width=True, type="primary")

    # Fetch data
    if fetch_clicked:
        if city.strip():
            with st.spinner(f"Fetching weather data for {city}..."):
                data = fetch_weather(city, unit)
                # set symbols based on unit
                if data:
                    unit_symbol = "°C" if unit == "metric" else "°F"
                    speed_unit = "m/s" if unit == "metric" else "mph"

                    # Save data in session state to use later for displaying
                    st.session_state.weather_data = {
                        "City": data["name"],
                        "Country Code": data["sys"]["country"],
                        "Temperature": f"{data['main']['temp']} {unit_symbol}",
                        "Feels Like": f"{data['main']['feels_like']} {unit_symbol}",
                        "Min Temperature": f"{data['main']['temp_min']} {unit_symbol}",
                        "Max Temperature": f"{data['main']['temp_max']} {unit_symbol}",
                        "Humidity": f"{data['main']['humidity']}%",
                        "Weather": data["weather"][0]["description"].title(),
                        "Wind Speed": f"{data['wind']['speed']} {speed_unit}",
                        "Pressure": f"{data['main']['pressure']} hPa",
                        "Visibility": f"{data.get('visibility', 'N/A')} meters",
                        "Latitude": data["coord"]["lat"],
                        "Longitude": data["coord"]["lon"],
                        "Fetched At": datetime.utcnow().isoformat()
                    }

                    # Store in SQLite database
                    insert_weather_data(st.session_state.weather_data)
                    st.success(f"Weather data fetched for {data['name']}")

                else:
                    st.error("City not found or API error. Please check the city name and try again.")
        else:
            st.warning("Please enter a city name")

    # Use weather data from session state for multiple purposes like to display as dataframe/json view, save as csv/json
    if st.session_state.weather_data:
        st.divider()
        
        # display as dataframe
        # Convert weather_data dict to DataFrame
        weather_df = pd.DataFrame(
            st.session_state.weather_data.items(),
            columns=["Parameter", "Value"]
        )
        # now display the dataframe using st.dataframe
        st.subheader("Weather Summary")
        st.dataframe(weather_df, use_container_width=True)

        # display as json
        # Expandable json view
        with st.expander("JSON View"):
            st.json(st.session_state.weather_data)


        # save as csv button
        if st.button("Save Data (CSV)", use_container_width=True):
            try:
                filename = save_to_csv(st.session_state.weather_data)
                st.success("Data saved successfully!")
                if filename:
                    st.info(f"File: {filename}")
            except Exception as e:
                st.error(f"Error saving file: {str(e)}")


        # Save as json button
        if st.button("Save Data (JSON)", use_container_width=True, type="primary"):
            try:
                filename = save_to_json(st.session_state.weather_data)
                st.success("Data saved successfully!")
                if filename:
                    st.info(f"File: {filename}")
            except Exception as e:
                st.error(f"Error saving file: {str(e)}")


# Main app layout 

# Show appropriate UI based on login state
if not st.session_state.logged_in:
    login_ui()
else:
    weather_ui()