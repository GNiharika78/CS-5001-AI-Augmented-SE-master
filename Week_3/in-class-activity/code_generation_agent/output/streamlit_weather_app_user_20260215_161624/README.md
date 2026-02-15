# Streamlit Weather App

A simple weather application that displays current weather and a 5-day forecast for any city. The app uses OpenWeatherMap API when available, with a deterministic demo mode as fallback.

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Run

Start the Streamlit app:
```bash
streamlit run src/main.py
```

## Example Usage

1. Enter a city name (e.g., "London")
2. View current weather and 5-day forecast
3. If no API key is configured, the app shows deterministic demo data

## Project Structure

```
.
├── README.md
├── requirements.txt
├── src/
│   └── main.py
└── tests/
    └── test_main.py
```

## Configuration

For live weather data:
1. Create a `secrets.toml` file in `.streamlit/`
2. Add your OpenWeatherMap API key:
```toml
[openweathermap]
api_key = "your_api_key_here"
```

Without an API key, the app runs in deterministic demo mode that varies by city name.
