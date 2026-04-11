"""
Shear resistance calculations for Kerto-Ripa elements according to ETA-07/0029.
"""

from app.domain.kertoripa.geometry import KertoRipaGeometryData
from app.domain.kertoripa.materials import KERTO_Q, KERTO_S

def calculate_shear_resistances(geom: KertoRipaGeometryData) -> dict[str, float | str]:
    """
    Calculates shear resistance R_V,k (characteristic) in kN for a single web/rib.
    Returns the partial resistances in a dict, and the governing minimum.
    """
    EI = geom.EI_ef_ULS
    if EI <= 0:
        return {"R_V_k_governing": 0.0, "failure_mode": "Invalid Geometry"}

    res = {}
    
    k_gl = 1.3 # Glue factor constant per ETA
    
    # Kerto-Q rolling shear strength is used for the glued connection to the web (ETA Eq A.22/A.24)
    f_v_0_flat_Q_k = KERTO_Q["f_v_0_flat_k"]
    
    # 1. Shear resistance of the glued connection between top slab and web (Eq A.22)
    # R_V,top,k = min( k_gl * b_2,eff,t * f_v,0,flat * EI / (E_1 * A_1 * a_1), b_w * f_v_0_flat * EI / (E_1 * A_1 * a_1) )
    if geom.E_top > 0 and geom.a1_ULS > 0:
        A_1 = geom.b_ef_top_ULS * (geom.cs.h_f1_mm or 0.0)
        denom_top = geom.E_top * A_1 * geom.a1_ULS
        
        if denom_top > 0:
            # Effective width for shear in the slab
            b_2_eff_t = min(geom.cs.b_w_mm + (geom.cs.h_f1_mm or 0.0), geom.b_ef_top_ULS)
            
            R_v_top_1 = (k_gl * b_2_eff_t * f_v_0_flat_Q_k * EI) / denom_top
            R_v_top_2 = (geom.cs.b_w_mm * f_v_0_flat_Q_k * EI) / denom_top
            res["R_V_top_k"] = min(R_v_top_1, R_v_top_2)

    # 2. Shear resistance of the glued connection between bottom slab and web (Eq A.24)
    if geom.E_bot > 0 and geom.a3_ULS > 0:
        A_3 = geom.b_ef_bot_ULS * (geom.cs.h_f2_mm or 0.0)
        denom_bot = geom.E_bot * A_3 * geom.a3_ULS
        
        if denom_bot > 0:
            # Bottom slab is Kerto-S in Open Box, where flatwise shear is 2.3 MPa. Else Kerto-Q.
            fv_flat_bot = KERTO_S["f_v_0_flat_k"] if geom.cs.section_type == "open_box" else KERTO_Q["f_v_0_flat_k"]
            
            b_2_eff_b = min(geom.cs.b_w_mm + (geom.cs.h_f2_mm or 0.0), geom.b_ef_bot_ULS)
            
            R_v_bot_1 = (k_gl * b_2_eff_b * fv_flat_bot * EI) / denom_bot
            R_v_bot_2 = (geom.cs.b_w_mm * fv_flat_bot * EI) / denom_bot
            res["R_V_bot_k"] = min(R_v_bot_1, R_v_bot_2)

    # 3. Shear resistance of the web (Eq A.23)
    f_v_0_edge_S_k = KERTO_S["f_v_0_edge_k"]
    h_w = geom.cs.h_w_mm
    b_w = geom.cs.b_w_mm
    
    # Calculate equivalent static moment (S_eq) at the neutral axis
    S_top_slab = 0.0
    if geom.E_top > 0:
        S_top_slab = geom.E_top * (geom.b_ef_top_ULS * (geom.cs.h_f1_mm or 0.0)) * geom.a1_ULS
        
    S_web = geom.E_web * (b_w / 2.0) * ((h_w / 2.0)**2 - geom.a2_ULS**2)
    
    S_eq = S_top_slab + S_web
    
    if S_eq > 0:
        res["R_V_web_k"] = (f_v_0_edge_S_k * b_w * EI) / S_eq

    # Convert all from N to kN
    for k in res:
        res[k] = res[k] * 1e-3
        
    check_keys = ["R_V_top_k", "R_V_bot_k", "R_V_web_k"]
    valid_checks = {k: v for k, v in res.items() if k in check_keys}
    
    if valid_checks:
        gov_key = min(valid_checks, key=valid_checks.get)
        res["R_V_k_governing"] = valid_checks[gov_key]
        res["failure_mode"] = gov_key
    else:
        res["R_V_k_governing"] = 0.0
        res["failure_mode"] = "N/A"
        
    return res
