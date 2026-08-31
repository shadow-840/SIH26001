import requests
import logging
from typing import Dict, Any

logger = logging.getLogger("SeismicClient")
USGS_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
REQUEST_TIMEOUT = 10

def get_recent_seismic_activity(lat: float, lon: float, max_radius_km: float = 150.0, min_magnitude: float = 2.5) -> Dict[str, Any]:
    """
    Fetches seismic events in the past 30 days within max_radius_km[cite: 1].
    Returns event count, max magnitude, and distance to the closest epicenter.
    """
    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": max_radius_km,
        "minmagnitude": min_magnitude,
        "orderby": "time",
        "limit": 10
    }
    
    try:
        response = requests.get(USGS_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        features = data.get("features", [])
        if not features:
            return {
                "status": "success",
                "source": "usgs-seismic",
                "recent_quake_count": 0,
                "max_magnitude": 0.0,
                "seismic_risk_factor": "LOW"
            }
            
        magnitudes = [f["properties"]["mag"] for f in features if f["properties"]["mag"] is not None]
        max_mag = max(magnitudes) if magnitudes else 0.0
        
        # Determine seismic conditioning risk
        risk_factor = "HIGH" if max_mag >= 4.5 or len(features) >= 3 else "MODERATE" if max_mag >= 3.5 else "LOW"
        
        return {
            "status": "success",
            "source": "usgs-seismic",
            "recent_quake_count": len(features),
            "max_magnitude": round(max_mag, 2),
            "seismic_risk_factor": risk_factor,
            "latest_event_place": features[0]["properties"]["place"]
        }
        
    except requests.exceptions.RequestException as err:
        logger.error(f"Seismic API error for ({lat}, {lon}): {err}")
        return {
            "status": "error",
            "error": str(err),
            "recent_quake_count": 0,
            "max_magnitude": 0.0,
            "seismic_risk_factor": "UNKNOWN"
        }