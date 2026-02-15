from typing import Dict, List, Optional
import os
import streamlit as st
import requests

def fetch_weather(city: str, api_key: str) -> Dict:
    """Fetch current weather and 5-day forecast from OpenWeatherMap API.

    Args:
        city: City name to fetch weather for.
        api_key: OpenWeatherMap API key.

    Returns:
        Dictionary with 'current' (temp, conditions) and 'forecast' (list of 5-day entries).

    Raises:
        ValueError: If API request fails or city not found.
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        current = {
            "temp": data["main"]["temp"],
            "conditions": data["weather"][0]["description"]
        }

        # Fetch 5-day forecast
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        forecast_params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "cnt": 5  # 5-day forecast (3-hour intervals)
        }
        forecast_response = requests.get(forecast_url, params=forecast_params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        forecast = []
        for item in forecast_data["list"]:
            forecast.append({
                "date": item["dt_txt"],
                "temp": item["main"]["temp"],
                "conditions": item["weather"][0]["description"]
            })

        return {"current": current, "forecast": forecast}

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Weather API request failed: {str(e)}")

def generate_demo(city: str) -> Dict:
    """Generate deterministic demo weather data based on city name.

    Args:
        city: City name to generate demo for.

    Returns:
        Dictionary with 'current' (temp, conditions) and 'forecast' (list of 5-day entries).
    """
    # Simple hash-based deterministic values
    hash_val = sum(ord(c) for c in city) % 100

    current_temp = 15 + (hash_val % 20) - 10
    current_conditions = ["Sunny", "Cloudy", "Rainy", "Snowy", "Foggy"][hash_val % 5]

    forecast = []
    for i in range(5):
        day_temp = current_temp + (i - 2) * 2  # Varies slightly each day
        day_conditions = ["Sunny", "Cloudy", "Rainy", "Snowy", "Foggy"][(hash_val + i) % 5]
        forecast.append({
            "date": f"2023-01-{i+1:02d}",
            "temp": day_temp,
            "conditions": day_conditions
        })

    return {"current": {"temp": current_temp, "conditions": current_conditions}, "forecast": forecast}

def render_ui():
    """Render Streamlit UI for weather app."""
    st.title("Weather Forecast App")

    # Get API key safely
    api_key = None
    try:
        api_key = st.secrets.get("OPENWEATHER_API_KEY")
    except Exception:
        api_key = None

    # User input
    city = st.text_input("Enter city name:", "")

    if not city:
        st.warning("Please enter a city name.")
        return

    try:
        if api_key:
            weather_data = fetch_weather(city, api_key)
            st.success("Using real weather data from OpenWeatherMap")
        else:
            weather_data = generate_demo(city)
            st.info("Using demo weather data (API key not configured)")

        # Display current weather
        st.subheader("Current Weather")
        st.write(f"Temperature: {weather_data['current']['temp']}°C")
        st.write(f"Conditions: {weather_data['current']['conditions']}")

        # Display forecast
        st.subheader("5-Day Forecast")
        for day in weather_data['forecast']:
            st.write(f"{day['date']}: {day['temp']}°C, {day['conditions']}")

    except ValueError as e:
        st.error(f"Error: {str(e)}")
        st.info("Falling back to demo data...")
        weather_data = generate_demo(city)
        st.subheader("Demo 5-Day Forecast")
        for day in weather_data['forecast']:
            st.write(f"{day['date']}: {day['temp']}°C, {day['conditions']}")

if __name__ == "__main__":
    render_ui()
