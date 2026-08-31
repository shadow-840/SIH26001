import requests
import logging
from typing import Dict, Any

logger = logging.getLogger("GeocodingClient")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
REQUEST_TIMEOUT = 10

def get_location_hierarchy(lat: float, lon: float) -> Dict[str, Any]:
    """
    Converts GPS coordinates into District, State, and Village/Town name.
    """
    headers = {"User-Agent": "SIH26001-LandslideEWS-Pipeline/1.0"}
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "zoom": 14
    }
    
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        address = data.get("address", {})
        district = (
            address.get("state_district") or 
            address.get("county") or 
            address.get("district") or 
            "Unknown District"
        )
        state = address.get("state", "North Eastern Region")
        locality = address.get("village") or address.get("town") or address.get("suburb") or address.get("city") or "Local Area"
        
        return {
            "status": "success",
            "source": "osm-nominatim",
            "display_name": data.get("display_name", ""),
            "locality": locality,
            "district": district,
            "state": state
        }
        
    except requests.exceptions.RequestException as err:
        logger.error(f"Geocoding failure: {err}")
        return {
            "status": "error",
            "error": str(err),
            "locality": "Unknown",
            "district": "Unknown District",
            "state": "Unknown State"
        }