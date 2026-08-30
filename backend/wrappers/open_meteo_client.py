import requests
import logging
from typing import Dict, Any

# Configure logger
logger = logging.getLogger("MeteoClient")
BASE_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10  # seconds

def _execute_request(lat: float, lon: float, hourly_vars: list, forecast_days: int) -> Dict[str, Any]:
    """Internal HTTP handler with error isolation."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": hourly_vars,
        "forecast_days": forecast_days,
        "timezone": "auto"
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return {
            "status": "success",
            "data": data.get("hourly", {})
        }
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to Open-Meteo for ({lat}, {lon})")
        return {"status": "error", "error": "Request timed out", "data": {}}
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP error {err.response.status_code} for ({lat}, {lon})")
        return {"status": "error", "error": f"HTTP {err.response.status_code}", "data": {}}
    except requests.exceptions.RequestException as err:
        logger.error(f"Network failure for ({lat}, {lon}): {err}")
        return {"status": "error", "error": "Network connection error", "data": {}}
    except Exception as err:
        logger.error(f"Unexpected error for ({lat}, {lon}): {err}")
        return {"status": "error", "error": str(err), "data": {}}


def get_precipitation(lat: float, lon: float, forecast_days: int = 2) -> Dict[str, Any]:
    """
    Fetches real-time and forecasted precipitation metrics.
    Returns hourly arrays for precipitation, precipitation_probability, and showers.
    """
    variables = ["precipitation", "precipitation_probability", "showers"]
    result = _execute_request(lat, lon, variables, forecast_days)
    
    if result["status"] == "success":
        hourly = result["data"]
        return {
            "status": "success",
            "source": "open-meteo",
            "units": {"precipitation": "mm", "precipitation_probability": "%"},
            "time": hourly.get("time", []),
            "precipitation": hourly.get("precipitation", []),
            "precipitation_probability": hourly.get("precipitation_probability", []),
            "showers": hourly.get("showers", [])
        }
    return result


def get_soil_moisture(lat: float, lon: float, forecast_days: int = 2) -> Dict[str, Any]:
    """
    Fetches volumetric water content across 3 critical subsurface layers[cite: 1].
    Returns hourly arrays for 0-10cm, 10-40cm, and 40-100cm depths.
    """
    variables = [
        "soil_moisture_0_to_10cm",
        "soil_moisture_10_to_40cm",
        "soil_moisture_40_to_100cm"
    ]
    result = _execute_request(lat, lon, variables, forecast_days)
    
    if result["status"] == "success":
        hourly = result["data"]
        return {
            "status": "success",
            "source": "open-meteo",
            "units": {"soil_moisture": "m³/m³"},
            "time": hourly.get("time", []),
            "soil_moisture_0_to_10cm": hourly.get("soil_moisture_0_to_10cm", []),
            "soil_moisture_10_to_40cm": hourly.get("soil_moisture_10_to_40cm", []),
            "soil_moisture_40_to_100cm": hourly.get("soil_moisture_40_to_100cm", [])
        }
    return result


def get_atmospheric_forcing(lat: float, lon: float, forecast_days: int = 2) -> Dict[str, Any]:
    """
    Fetches surface meteorological forcing metrics[cite: 1].
    Returns hourly arrays for 2m temperature, 10m wind speed, and surface pressure.
    """
    variables = ["temperature_2m", "wind_speed_10m", "surface_pressure"]
    result = _execute_request(lat, lon, variables, forecast_days)
    
    if result["status"] == "success":
        hourly = result["data"]
        return {
            "status": "success",
            "source": "open-meteo",
            "units": {"temperature": "°C", "wind_speed": "km/h", "surface_pressure": "hPa"},
            "time": hourly.get("time", []),
            "temperature_2m": hourly.get("temperature_2m", []),
            "wind_speed_10m": hourly.get("wind_speed_10m", []),
            "surface_pressure": hourly.get("surface_pressure", [])
        }
    return result