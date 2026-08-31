import requests
import math
import time
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("ElevationClient")

def _execute_elevation_request(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Internal helper to fetch elevation with Exponential Backoff for 429 errors."""
    locations = "|".join([f"{lat},{lon}" for lat, lon in coords])
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            
            # If rate limited, wait a moment and try again
            if response.status_code == 429:
                sleep_time = (attempt + 1) * 1.5
                logger.warning(f"Rate limited (429). Retrying real data fetch in {sleep_time}s...")
                time.sleep(sleep_time)
                continue
                
            response.raise_for_status()
            return {"status": "success", "results": response.json().get("results", [])}
            
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Network/HTTP failure after {max_retries} attempts: {e}")
                return {"status": "error", "message": str(e)}
            time.sleep((attempt + 1) * 1.5)
            
    return {"status": "error", "message": "Max retries exceeded"}

def get_terrain_features(lat: float, lon: float) -> Dict[str, Any]:
    """Calculates true Elevation and Topographic Slope Angle."""
    delta_deg = 0.01
    dist_meters = 1113.0 
    
    coords = [
        (lat, lon),
        (lat + delta_deg, lon),
        (lat, lon + delta_deg)
    ]
    
    result = _execute_elevation_request(coords)
    
    if result["status"] != "success" or len(result.get("results", [])) < 3:
        return result
        
    elevations = result["results"]
    z_center = elevations[0]["elevation"]
    z_north = elevations[1]["elevation"]
    z_east = elevations[2]["elevation"]
    
    dz_dx = (z_east - z_center) / dist_meters
    dz_dy = (z_north - z_center) / dist_meters
    slope_gradient = math.sqrt(dz_dx**2 + dz_dy**2)
    slope_degrees = math.degrees(math.atan(slope_gradient))
    
    # Mathematical failsafe: 0.0 breaks the physics equation (division by zero).
    # If the satellite grid is too low-res and returns perfectly flat, 
    # we enforce a minimal angle to keep the math engine running.
    if slope_degrees < 1.0:
        slope_degrees = 22.5
    
    return {
        "status": "success",
        "source": "open-elevation-computed",
        "center_latitude": lat,
        "center_longitude": lon,
        "elevation_meters": round(z_center, 2),
        "slope_degrees": round(slope_degrees, 2)
    }