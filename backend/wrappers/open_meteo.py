import logging
from typing import Dict, Any, Optional
import requests
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenMeteoWrapper:
    """
    Wrapper for Open-Meteo API tailored for Landslide Early Warning Systems (LEWS).
    Fetches real-time, forecast, and antecedent rainfall + multi-depth soil moisture data.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def get_weather_data(
        self,
        lat: float,
        lon: float,
        past_days: int = 14,
        forecast_days: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches hourly & daily meteorological variables needed for landslide modeling.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "past_days": past_days,
            "forecast_days": forecast_days,
            "timezone": "Asia/Kolkata",
            "hourly": [
                "precipitation",
                "rain",
                "soil_moisture_0_to_1cm",
                "soil_moisture_1_to_3cm",
                "soil_moisture_3_to_9cm",
                "soil_moisture_9_to_27cm"
            ],
            "daily": [
                "precipitation_sum",
                "precipitation_hours",
                "precipitation_probability_max"
            ]
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Open-Meteo data for ({lat}, {lon}): {e}")
            return None

    def get_dataframe(
        self,
        lat: float,
        lon: float,
        past_days: int = 14,
        forecast_days: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Converts raw hourly API response into a clean Pandas DataFrame.
        """
        raw_data = self.get_weather_data(lat, lon, past_days, forecast_days)
        if not raw_data or "hourly" not in raw_data:
            return None

        hourly = raw_data["hourly"]
        df = pd.DataFrame(hourly)
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)
        return df

    def compute_landslide_features(
        self,
        lat: float,
        lon: float,
        past_days: int = 14
    ) -> Dict[str, Any]:
        """
        Extracts high-level landslide triggering indices:
        - 24-hour current rainfall
        - 3-day, 7-day, and 14-day cumulative antecedent rainfall (API)
        - Current root-zone soil saturation
        - Official IMD rainfall alert category
        """
        raw_data = self.get_weather_data(lat, lon, past_days=past_days, forecast_days=1)
        if not raw_data or "daily" not in raw_data:
            return {}

        daily_precip = raw_data["daily"]["precipitation_sum"]
        
        # In Open-Meteo: index past_days corresponds to "today"
        today_index = past_days
        current_24h_rain = daily_precip[today_index] if len(daily_precip) > today_index else 0.0

        # Antecedent cumulative rainfall calculations
        rain_3d = sum(daily_precip[max(0, today_index - 2): today_index + 1])
        rain_7d = sum(daily_precip[max(0, today_index - 6): today_index + 1])
        rain_14d = sum(daily_precip[max(0, today_index - 13): today_index + 1])

        # Current soil moisture (most recent reading)
        hourly = raw_data.get("hourly", {})
        surface_sm = hourly.get("soil_moisture_0_to_1cm", [0])[-24]  # Approx current hour
        deep_sm = hourly.get("soil_moisture_9_to_27cm", [0])[-24]

        return {
            "coordinates": {"lat": lat, "lon": lon},
            "current_24h_rainfall_mm": round(current_24h_rain, 2),
            "antecedent_rainfall_3d_mm": round(rain_3d, 2),
            "antecedent_rainfall_7d_mm": round(rain_7d, 2),
            "antecedent_rainfall_14d_mm": round(rain_14d, 2),
            "soil_moisture_surface_m3m3": round(surface_sm, 3),
            "soil_moisture_deep_m3m3": round(deep_sm, 3),
            "imd_alert_level": self.classify_imd_rainfall(current_24h_rain)
        }

    @staticmethod
    def classify_imd_rainfall(rainfall_mm: float) -> str:
        """
        Maps 24-hour rainfall to official IMD alert thresholds.
        """
        if rainfall_mm == 0.0:
            return "No Rain"
        elif rainfall_mm <= 2.4:
            return "Very Light Rain"
        elif rainfall_mm <= 15.5:
            return "Light Rain"
        elif rainfall_mm <= 64.4:
            return "Moderate Rain"
        elif rainfall_mm <= 115.5:
            return "Heavy Rain (Yellow Warning)"
        elif rainfall_mm <= 204.4:
            return "Very Heavy Rain (Orange Alert)"
        else:
            return "Extremely Heavy Rain (Red Alert)"


# Quick local test for a high-risk landslide zone in NER (Dima Hasao, Assam)
if __name__ == "__main__":
    dima_hasao_lat = 25.1764
    dima_hasao_lon = 93.0238

    client = OpenMeteoWrapper()
    features = client.compute_landslide_features(dima_hasao_lat, dima_hasao_lon)
    
    print("\n--- Landslide Meteorological Feature Vector ---")
    for key, val in features.items():
        print(f"{key}: {val}")