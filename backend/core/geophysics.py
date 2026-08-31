import math

def calculate_factor_of_safety(slope_deg: float, volumetric_water_content: float) -> float:
    """
    Calculates the transient Factor of Safety (FoS) based on the infinite slope model.
    Values < 1.0 indicate slope failure.
    """
    if slope_deg <= 0.5:
        return 99.0  # Flat terrain is unconditionally stable
        
    # 1. Geotechnical constants (Averaged for NER vulnerable soils)
    c_prime = 10.5       # Effective cohesion in kPa (Typical range: 9.29 to 11.45)[cite: 1]
    phi_prime_deg = 17.0 # Internal friction angle (Typical range: 15.58 to 18.43)[cite: 1]
    gamma_t = 18.0       # Total unit weight of soil in kN/m³
    Z = 2.5              # Depth of potential failure plane in meters
    
    alpha = math.radians(slope_deg)
    phi_prime = math.radians(phi_prime_deg)
    
    # 2. Calculate Pore Water Pressure (u_w) from API Soil Moisture
    # Friction diminishes rapidly as water content exceeds 25% (0.25 m³/m³)[cite: 1]
    if volumetric_water_content > 0.25:
        # Simplified transient pressure heuristic: scales rapidly after saturation point
        u_w = (volumetric_water_content - 0.25) * 45.0 
    else:
        u_w = 0.0
        
    # 3. Calculate Stresses[cite: 1]
    # Total normal stress: σ = γt * Z * cos²(α)
    total_normal_stress = gamma_t * Z * (math.cos(alpha)**2)
    
    # Effective stress: σ' = σ - u_w
    effective_stress = max(0.0, total_normal_stress - u_w)
    
    # Resisting Force (Shear Strength): τf = c' + σ' * tan(φ')
    shear_strength = c_prime + (effective_stress * math.tan(phi_prime))
    
    # Driving Force (Shear Stress): τ = γt * Z * sin(α) * cos(α)
    shear_stress = gamma_t * Z * math.sin(alpha) * math.cos(alpha)
    
    # 4. Factor of Safety
    if shear_stress <= 0:
        return 99.0
        
    fos = shear_strength / shear_stress
    return round(fos, 3)