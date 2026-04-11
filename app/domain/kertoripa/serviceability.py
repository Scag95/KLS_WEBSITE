"""
Deflection and Serviceability calculations (SLS) for Kerto-Ripa elements.
"""

from app.domain.kertoripa.geometry import KertoRipaGeometryData
from app.domain.kertoripa.materials import KERTO_S

def calculate_deflections(geom: KertoRipaGeometryData, line_load_kN_per_m: float) -> dict[str, float]:
    """
    Calculates instantaneous deflections (w_inst) under a given line load in mm.
    Input load is in kN/m.
    """
    L_ef = geom.span.L_ef_mm
    
    # Bending deflection (w_inst,M)
    EI = geom.EI_ef_SLS
    if EI <= 0:
        return {"u_inst_M_mm": 0.0, "u_inst_V_mm": 0.0, "u_inst_total_mm": 0.0}
        
    u_inst_M = (5.0 * line_load_kN_per_m * L_ef**4) / (384.0 * EI)
    
    # Shear deflection (w_inst,V)
    A_web = geom.cs.h_w_mm * geom.cs.b_w_mm
    G_web = KERTO_S["G_mean"]
    
    u_inst_V = (line_load_kN_per_m * L_ef**2) / (8.0 * G_web * A_web) if A_web > 0 else 0.0
    
    u_inst_total = u_inst_M + u_inst_V
    
    return {
        "u_inst_M_mm": u_inst_M,
        "u_inst_V_mm": u_inst_V,
        "u_inst_total_mm": u_inst_total
    }

def calculate_final_deflection(
    u_inst_g_mm: float, 
    u_inst_q_mm: float, 
    k_def: float, 
    psi_2: float
) -> float:
    """
    Calculates the final deflection net_fin in mm.
    Since combinations logic handles psi_2 pre-multiplied for Quasi-Permanent combos,
    the psi_2 factor passed here is usually 1.0 (already absorbed by Q).
    """
    u_fin_g = u_inst_g_mm * (1.0 + k_def)
    u_fin_q = u_inst_q_mm * (1.0 + psi_2 * k_def)
    return u_fin_g + u_fin_q
