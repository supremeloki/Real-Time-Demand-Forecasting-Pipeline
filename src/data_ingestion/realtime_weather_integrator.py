import logging
import requests
from datetime import datetime, timedelta
import random
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RealtimeWeatherIntegrator:
    """
    Fetches real-time weather data for a given location (geohash/coordinates).
    For demo purposes, it simulates API calls and returns mock data.
    """

    def __init__(
        self,
        api_key: str = "DUMMY_API_KEY",
        base_url: str = "https://api.weather.com/v1/forecast/hourly/10day.json",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.last_fetch_time: Dict[str, datetime] = (
            {}
        )  # Cache last fetch time per location
        self.cache_duration = timedelta(
            minutes=15
        )  # Only refetch if older than 15 mins
        self.weather_cache: Dict[str, Dict[str, Any]] = {}

        logging.info("RealtimeWeatherIntegrator initialized.")

    def _convert_geohash_to_coords(self, geohash_id: str) -> Dict[str, float]:
        """
        Mocks converting a geohash to latitude and longitude.
        In a real system, you'd use a geohash library (e.g., python-geohash).
        """
        # Example for Tehran (approx center: 35.7, 51.4)
        # Randomize slightly based on geohash to simulate different areas
        random.seed(hash(geohash_id))  # Consistent randomness for same geohash
        lat = 35.7 + random.uniform(-0.1, 0.1)
        lon = 51.4 + random.uniform(-0.1, 0.1)
        return {"lat": lat, "lon": lon}

    def _fetch_weather_from_api(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Mocks an external API call to fetch current weather data.
        """
        logging.info(f"Mocking API call for weather at ({lat:.2f}, {lon:.2f}).")
        # Simulate network delay
        # import time; time.sleep(0.1)

        # Generate realistic-ish mock weather data
        temperature = random.uniform(5, 30)
        humidity = random.uniform(40, 95)
        precipitation = random.choices(
            [0.0, 0.1, 0.5, 2.0, 5.0], weights=[0.7, 0.2, 0.05, 0.04, 0.01]
        )[0]
        weather_condition = random.choice(
            ["Clear", "Cloudy", "Partly Cloudy", "Rain", "Fog"]
        )
        wind_speed = random.uniform(0, 20)

        # Introduce some consistency with time of day, e.g., colder at night
        current_hour = datetime.now().hour
        if 0 <= current_hour < 6:  # Night
            temperature = random.uniform(temperature - 5, temperature + 2)
            precipitation *= 1.5  # More chance of fog/dew
        elif 12 <= current_hour < 18:  # Afternoon
            temperature = random.uniform(temperature - 2, temperature + 5)

        # Clamp temperature for realism
        temperature = max(-10, min(40, temperature))

        return {
            "temperature_celsius": round(temperature, 1),
            "humidity_percent": round(humidity, 1),
            "precipitation_mm": round(precipitation, 1),
            "weather_condition": weather_condition,
            "wind_speed_kph": round(wind_speed, 1),
            "last_updated": datetime.now().isoformat(),
        }

    def get_weather_data(self, geohash_id: str) -> Dict[str, Any]:
        """
        Retrieves current weather data for a given geohash, using caching.
        """
        current_time = datetime.now()

        # Check cache
        if (
            geohash_id in self.weather_cache
            and current_time - self.last_fetch_time.get(geohash_id, datetime.min)
            < self.cache_duration
        ):
            logging.info(f"Returning cached weather data for {geohash_id}.")
            return self.weather_cache[geohash_id]

        logging.info(f"Fetching fresh weather data for {geohash_id}.")
        coords = self._convert_geohash_to_coords(geohash_id)
        weather_data = self._fetch_weather_from_api(coords["lat"], coords["lon"])

        # Update cache
        self.weather_cache[geohash_id] = weather_data
        self.last_fetch_time[geohash_id] = current_time

        return weather_data


if __name__ == "__main__":
    weather_integrator = RealtimeWeatherIntegrator()

    test_geohashes = ["dr5ru", "dr5ry", "dr5rz", "dr5rg"]

    print("--- Simulating Real-time Weather Integration ---")
    for gh in test_geohashes:
        weather = weather_integrator.get_weather_data(gh)
        print(f"\nWeather for {gh}:")
        for k, v in weather.items():
            print(f"  {k}: {v}")

    # Simulate a second fetch for the same geohash within cache duration
    print("\n--- Fetching again for dr5ru (should be cached) ---")
    weather_cached = weather_integrator.get_weather_data("dr5ru")
    print(
        f"Cached Weather for dr5ru: {weather_cached['temperature_celsius']}°C, {weather_cached['weather_condition']}"
    )

    # Simulate waiting past cache duration (e.g., 20 mins)
    print("\n--- Simulating time passing for a fresh fetch ---")
    import time

    time.sleep(1)  # simulate some minimal delay
    weather_integrator.last_fetch_time["dr5ru"] = datetime.now() - timedelta(
        minutes=20
    )  # Force cache invalidation

    weather_fresh = weather_integrator.get_weather_data("dr5ru")
    print(
        f"Fresh Weather for dr5ru: {weather_fresh['temperature_celsius']}°C, {weather_fresh['weather_condition']}"
    )
