"""
Support compression calculations for Kerto-Ripa elements according to ETA-07/0029.
"""

from app.domain.kertoripa.geometry import KertoRipaGeometryData
from app.domain.kertoripa.materials import KERTO_Q, KERTO_S

def calculate_support_resistance(geom: KertoRipaGeometryData) -> dict[str, float]:
    """
    Calculates support compression resistance R_c,90,k in kN for a single web/rib.
    Based on A.32, A.33, A.34 ETA-07/0029.
    """
    res = {}
    
    L_support = geom.span.L_support_mm
    b_w = geom.cs.b_w_mm
    
    # Effective bearing length: L_support is spread by 15 mm (Eq A.33 logic standard EC5)
    l_c_90_ef = L_support + 15.0
    
    k_c_90 = 1.0 # default
    
    # Check if there's a bottom slab resting on the support
    if geom.cs.h_f2_mm:
        # According to standard rules for Kerto-Q flanges bearing on supports
        if geom.cs.h_f2_mm < 33:
            if geom.span.support_position == "end":
                k_c_90 = 1.2
            else:
                k_c_90 = 1.6
        else:
            k_c_90 = 1.0
            
        f_c_90_k = KERTO_Q["f_c_90_flat_k"]
    else:
        # No bottom slab. Web (Kerto-S) bears directly on support.
        # f_c_90,edge,S,k = 6.0 MPa
        f_c_90_k = KERTO_S["f_c_90_k"]
        if geom.span.support_position == "end":
            k_c_90 = 1.2
        else:
            k_c_90 = 1.2 # Standard EC5 logic for interior supports bearing on edge
            
    # Area of bearing per rib
    A_bearing = b_w * l_c_90_ef
    
    # Characteristic capacity
    R_c_90_k = k_c_90 * f_c_90_k * A_bearing
    
    res["R_c_90_k_governing"] = R_c_90_k * 1e-3  # Convert N to kN
    res["k_c_90_used"] = k_c_90
    res["failure_mode"] = "support_compression"
    
    return res
