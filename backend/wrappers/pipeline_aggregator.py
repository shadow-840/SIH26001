from wrappers.open_meteo_client import get_precipitation, get_soil_moisture, get_atmospheric_forcing
from wrappers.open_elevation_client import get_terrain_features
from wrappers.seismic_client import get_recent_seismic_activity
from wrappers.geocoding_client import get_location_hierarchy
from typing import Dict, Any
import logging

logger = logging.getLogger("MasterPipeline")

def collect_all_geospatial_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Single unified entrypoint:
    Aggregates Terrain, Hydrometeorological, Subsurface Moisture, Seismic, and Admin data.
    """
    # 1. Fetch Location Admin Hierarchy
    location = get_location_hierarchy(lat, lon)
    
    # 2. Fetch Terrain (Elevation & Calculated Slope Angle)[cite: 1]
    terrain = get_terrain_features(lat, lon)
    
    # 3. Fetch Hydrometeorology & Soil Saturation[cite: 1]
    precip = get_precipitation(lat, lon, forecast_days=2)
    soil = get_soil_moisture(lat, lon, forecast_days=2)
    atmos = get_atmospheric_forcing(lat, lon, forecast_days=2)
    
    # 4. Fetch Seismic Risk Profile[cite: 1]
    seismic = get_recent_seismic_activity(lat, lon)
    
    # Extract numerical series or apply safe defaults
    rain_series = precip.get("precipitation", [0.0] * 48) if precip.get("status") == "success" else [0.0] * 48
    soil_top_series = soil.get("soil_moisture_0_to_10cm", [0.25] * 48) if soil.get("status") == "success" else [0.25] * 48
    soil_deep_series = soil.get("soil_moisture_10_to_40cm", [0.30] * 48) if soil.get("status") == "success" else [0.30] * 48
    
    # Compute derived analytical features
    current_hourly_rain = rain_series[0] if rain_series else 0.0
    accumulated_24h_rain = sum(rain_series[:24])
    current_topsoil_moisture = soil_top_series[0] if soil_top_series else 0.25
    current_subsoil_moisture = soil_deep_series[0] if soil_deep_series else 0.30
    
    slope_deg = terrain.get("slope_degrees", 25.0) if terrain.get("status") == "success" else 25.0
    elevation_m = terrain.get("elevation_meters", 1000.0) if terrain.get("status") == "success" else 1000.0
    
    # Master JSON Schema
    unified_payload = {
        "meta": {
            "query_coordinates": {"latitude": lat, "longitude": lon},
            "location_name": f"{location.get('locality')}, {location.get('district')}, {location.get('state')}"
        },
        "geomorphology": {
            "slope_degrees": slope_deg,
            "elevation_meters": elevation_m,
            "seismic_risk": seismic.get("seismic_risk_factor", "LOW"),
            "recent_earthquakes_150km": seismic.get("recent_quake_count", 0)
        },
        "realtime_conditions": {
            "current_rain_mm_per_hr": round(current_hourly_rain, 2),
            "topsoil_moisture_m3_m3": round(current_topsoil_moisture, 3),
            "subsoil_moisture_m3_m3": round(current_subsoil_moisture, 3)
        },
        "forecast_24h": {
            "cumulative_rainfall_mm": round(accumulated_24h_rain, 2),
            "hourly_rainfall_projection": rain_series[:24]
        },
        "ml_feature_vector": [
            slope_deg,
            elevation_m,
            accumulated_24h_rain,
            current_topsoil_moisture,
            current_subsoil_moisture
        ]
    }
    
    return unified_payload

if __name__ == "__main__":
    # Test on Shillong, Meghalaya
    test_lat, test_lon = 25.5788, 91.8933
    import pprint
    data = collect_all_geospatial_data(test_lat, test_lon)
    pprint.pprint(data)