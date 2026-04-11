"""
Bending resistance calculations for Kerto-Ripa elements according to ETA-07/0029.
"""

from app.domain.kertoripa.geometry import KertoRipaGeometryData
from app.domain.kertoripa.materials import KERTO_Q, KERTO_S

def calculate_k_l(L_ef: float) -> float:
    """Eq (A.13): Length factor for tensile resistance."""
    if L_ef <= 0:
        return 1.1
    return min(1.1, (3000.0 / L_ef) ** 0.06)

def calculate_k_h(h_i: float) -> float:
    """Eq (A.15): Depth factor for bending resistance."""
    if h_i <= 0:
        return 1.2
    return min(1.2, (300.0 / h_i) ** 0.12)

def calculate_bending_resistances(geom: KertoRipaGeometryData) -> dict[str, float | str]:
    """
    Calculates bending moment resistance R_M,k (characteristic) in kNm.
    Returns the partial resistances in a dict, and the governing minimum.
    """
    EI = geom.EI_ef_ULS
    if EI <= 0:
         return {"R_M_k_governing": 0.0, "failure_mode": "Invalid Geometry"}

    res = {}
    
    # 1. Bending moment resistance based on mean compression stress in the middle of the flange (A.11)
    f_c_0_k_top = KERTO_Q["f_c_0_k"]
    E_top = geom.E_top
    if E_top > 0 and geom.a1_ULS > 0:
        res["R_M_c_top_k"] = (f_c_0_k_top * EI) / (E_top * geom.a1_ULS)
    
    f_c_0_k_bot = KERTO_Q["f_c_0_k"] if geom.cs.section_type != "open_box" else KERTO_S["f_c_0_k"]
    E_bot = geom.E_bot
    if E_bot > 0 and geom.a3_ULS > 0:
        res["R_M_c_bot_k"] = (f_c_0_k_bot * EI) / (E_bot * geom.a3_ULS)

    # 2. Bending moment resistance based on mean tension stress in the middle of the flange (A.12)
    k_l = calculate_k_l(geom.span.L_ef_mm)
    
    f_t_0_k_top = KERTO_Q["f_t_0_k"]
    if E_top > 0 and geom.a1_ULS > 0:
        res["R_M_t_top_k"] = (k_l * f_t_0_k_top * EI) / (E_top * geom.a1_ULS)
        
    f_t_0_k_bot = KERTO_Q["f_t_0_k"] if geom.cs.section_type != "open_box" else KERTO_S["f_t_0_k"]
    if E_bot > 0 and geom.a3_ULS > 0:
        res["R_M_t_bot_k"] = (k_l * f_t_0_k_bot * EI) / (E_bot * geom.a3_ULS)
        
    # 3. Bending moment resistance based on axial edge stress of the web (A.14)
    h_w = geom.cs.h_w_mm
    k_h = calculate_k_h(h_w)
    f_m_k_web = KERTO_S["f_m_k"]
    E_web = geom.E_web
    
    dist_top = abs(h_w / 2.0 - geom.a2_ULS)
    dist_bot = abs(h_w / 2.0 + geom.a2_ULS)
    
    if dist_top > 0:
        res["R_M_m_edge_top_k"] = (k_h * f_m_k_web * EI) / (E_web * dist_top)
    if dist_bot > 0:
        res["R_M_m_edge_bot_k"] = (k_h * f_m_k_web * EI) / (E_web * dist_bot)

    # 4. Centric bending moment resistance of the web (A.19)
    res["R_M_m_centric_k"] = (f_m_k_web * EI) / (E_web * (h_w / 2.0))
    
    # Convert from N*mm to kNm
    for k in res:
        res[k] = res[k] * 1e-6
        
    # Governing is the minimum of compressive, tensile, and axial edge stress capacities
    check_keys = ["R_M_c_top_k", "R_M_c_bot_k", "R_M_t_top_k", "R_M_t_bot_k", 
                  "R_M_m_edge_top_k", "R_M_m_edge_bot_k"]
    valid_checks = {k: v for k, v in res.items() if k in check_keys}
    
    if valid_checks:
        gov_key = min(valid_checks, key=valid_checks.get)
        res["R_M_k_governing"] = valid_checks[gov_key]
        res["failure_mode"] = gov_key
    else:
        res["R_M_k_governing"] = 0.0
        res["failure_mode"] = "N/A"
    
    return res
