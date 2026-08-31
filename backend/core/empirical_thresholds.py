def calculate_risk_index(current_rain_mm: float, soil_vwc: float, fos: float, seismic_risk: str) -> dict:
    """
    Evaluates real-time hazard levels using hierarchical multi-level logic gates[cite: 1].
    """
    # FoS approaches unity (1.0) = imminent failure[cite: 1]
    if fos <= 1.1 or (current_rain_mm >= 30.0 and soil_vwc >= 0.45):
        return {
            "level": "LEVEL 4: CRITICAL",
            "color": "#D32F2F", 
            "action": "Imminent slope failure detected. Immediate evacuation required."
        }
    
    # Subsurface moisture crosses safety limits and FoS is degrading[cite: 1]
    if fos <= 1.4 or (current_rain_mm >= 15.0 and soil_vwc >= 0.38) or (seismic_risk == "HIGH" and soil_vwc > 0.35):
        return {
            "level": "LEVEL 3: HIGH ALERT",
            "color": "#F57C00",
            "action": "Subsurface weakening active. Halt movement on hill roads."
        }
        
    # Increased probability of hazard based on surface metrics[cite: 1]
    if fos <= 1.8 or current_rain_mm >= 5.0 or soil_vwc >= 0.32:
        return {
            "level": "LEVEL 2: WATCH",
            "color": "#FBC02D",
            "action": "Elevated saturation. Monitor localized precipitation."
        }
        
    return {
        "level": "LEVEL 1: NORMAL",
        "color": "#388E3C",
        "action": "Conditions stable. Standard monitoring active."
    }