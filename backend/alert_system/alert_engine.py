from core.geophysics import calculate_factor_of_safety
from core.empirical_thresholds import calculate_risk_index
from typing import Dict, Any

class LandslideRiskEvaluator:
    
    def evaluate_realtime_empirical(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Routes payload data into the core mathematical models."""
        rain_now = data["realtime_conditions"]["current_rain_mm_per_hr"]
        subsoil = data["realtime_conditions"]["subsoil_moisture_m3_m3"]
        slope = data["geomorphology"]["slope_degrees"]
        seismic = data["geomorphology"]["seismic_risk"]
        
        # Calculate physics metric
        fos = calculate_factor_of_safety(slope, subsoil)
        
        # Calculate threshold gates
        result = calculate_risk_index(rain_now, subsoil, fos, seismic)
        
        result["metrics_evaluated"] = {
            "factor_of_safety": fos,
            "rainfall_rate_mm_h": rain_now,
            "subsoil_saturation": subsoil,
            "slope_deg": slope
        }
        
        return result