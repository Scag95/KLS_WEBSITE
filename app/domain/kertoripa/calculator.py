"""
Main orchestrator for Kerto-Ripa structural calculations.
"""

from __future__ import annotations

import math

from app.domain.combinations import generate_combinations
from app.schemas.actions import ActionType, CombinationType

from app.schemas.kertoripa import (
    KertoRipaCalculationRequest,
    KertoRipaCalculationResponse,
    KertoRipaGeometryResults,
    KertoRipaCheckResult,
    RibPosition,
)
from app.schemas.fem import (
    BeamAnalysisRequest,
    BeamSpanDefinition,
    BeamMaterial,
    BeamSection,
    DistributedLoad,
    DistributedLoadDirection,
    BeamTheory,
)
from app.domain.fem import analyze_beam

from app.schemas.floor_joist import WarningMessage

from app.domain.kertoripa.materials import (
    get_k_mod, 
    get_k_def, 
    GAMMA_M_LVL,
    KERTO_S,
)
from app.domain.kertoripa.geometry import KertoRipaGeometryData
from app.domain.kertoripa.bending import calculate_bending_resistances
from app.domain.kertoripa.shear import calculate_shear_resistances
from app.domain.kertoripa.support import calculate_support_resistance
from app.domain.kertoripa.serviceability import calculate_final_deflection

def _run_fem_analysis(span_m: float, supports: list, EI_Nmm2: float, line_loads: list[DistributedLoad]) -> dict:
    """Helper to run Euler-Bernoulli beam analysis leveraging fem.py. Returns summary object."""

    fem_req = BeamAnalysisRequest(
        beam_theory=BeamTheory.EULER_BERNOULLI,
        span=BeamSpanDefinition(length_m=span_m, element_count=max(20, int(span_m * 10))),
        stiffness_ei_Nmm2=EI_Nmm2,
        supports=supports,
        loads=line_loads
    )
    res = analyze_beam(fem_req)
    return res

def calculate_kerto_ripa(request: KertoRipaCalculationRequest) -> KertoRipaCalculationResponse:
    """Orchestrates the entire execution of the Kerto-Ripa checks with FEM engine."""
    warnings: list[WarningMessage] = []
    
    geom = KertoRipaGeometryData(request.cross_section, request.span, RibPosition.MIDDLE)
    
    geom_res = KertoRipaGeometryResults(
        b_f_mm=geom.b_f,
        b_ef_SLS_top_mm=geom.b_ef_top_SLS, b_ef_ULS_top_mm=geom.b_ef_top_ULS,
        b_ef_SLS_bot_mm=geom.b_ef_bot_SLS, b_ef_ULS_bot_mm=geom.b_ef_bot_ULS,
        EI_ef_SLS_Nmm2=geom.EI_ef_SLS, EI_ef_ULS_Nmm2=geom.EI_ef_ULS,
        neutral_axis_a2_mm=geom.a2_ULS,
    )
    
    k_def = get_k_def(request.design_basis.service_class)
    k_mod = get_k_mod(request.design_basis.load_duration_class, request.design_basis.service_class)
    
    bend_res = calculate_bending_resistances(geom)
    R_M_k = float(bend_res["R_M_k_governing"])
    
    shear_res = calculate_shear_resistances(geom)
    R_V_k = float(shear_res["R_V_k_governing"])
    
    support_res = calculate_support_resistance(geom)
    R_c_90_k = float(support_res["R_c_90_k_governing"])
    
    R_M_d = k_mod * R_M_k / GAMMA_M_LVL
    R_V_d = k_mod * R_V_k / GAMMA_M_LVL
    R_c_90_d = k_mod * R_c_90_k / GAMMA_M_LVL
    
    intermediate = {
        "k_mod": k_mod, "k_def": k_def, "gamma_m": GAMMA_M_LVL,
        "R_M_d": R_M_d, "R_V_d": R_V_d, "R_c_90_d": R_c_90_d,
        "bending_modes": bend_res, "shear_modes": shear_res, "support_modes": support_res,
    }
    
    combinations = generate_combinations(request.action_catalog)
    
    uls_checks: list[KertoRipaCheckResult] = []
    sls_checks: list[KertoRipaCheckResult] = []
    
    spacing_m = (geom.b_f + request.cross_section.b_w_mm) / 1000.0
    span_m = request.span.L_ef_mm / 1000.0
    
    passed_all = True
    max_uls_utilization = 0.0
    governing_uls_check_name = "None"
    
    # Area for shear calculation approx
    A_web = geom.cs.h_w_mm * geom.cs.b_w_mm
    G_web = KERTO_S["G_mean"]
    
    for comb in combinations.combinations:
        if comb.combination_type == CombinationType.ULS_FUNDAMENTAL:
            line_load_kN_m = sum(t.design_value_kN_per_m2 for t in comb.terms) * spacing_m
            
            fem_output = _run_fem_analysis(
                span_m=span_m,
                supports=request.supports,
                EI_Nmm2=geom.EI_ef_ULS,
                line_loads=[
                    DistributedLoad(start_m=0.0, end_m=span_m, value_kN_per_m=-line_load_kN_m, direction=DistributedLoadDirection.GLOBAL_Y)
                ]
            )
            
            M_d = fem_output.summary.max_moment_kNm
            V_d = fem_output.summary.max_shear_kN
            
            u_bend = M_d / R_M_d if R_M_d > 0 else float('inf')
            u_shear = V_d / R_V_d if R_V_d > 0 else float('inf')
            u_support = V_d / R_c_90_d if R_c_90_d > 0 else float('inf')
            
            combo_tag = comb.leading_action_id or "perm"
            
            uls_checks.append(KertoRipaCheckResult(
                check=f"bending_ULS_{combo_tag}", demand=M_d, capacity=R_M_d, 
                utilization=u_bend, unit="kNm", passed=u_bend <= 1.0, failure_mode=str(bend_res["failure_mode"])
            ))
            uls_checks.append(KertoRipaCheckResult(
                check=f"shear_ULS_{combo_tag}", demand=V_d, capacity=R_V_d, 
                utilization=u_shear, unit="kN", passed=u_shear <= 1.0, failure_mode=str(shear_res["failure_mode"])
            ))
            uls_checks.append(KertoRipaCheckResult(
                check=f"support_ULS_{combo_tag}", demand=V_d, capacity=R_c_90_d, 
                utilization=u_support, unit="kN", passed=u_support <= 1.0, failure_mode="support_compression"
            ))
            
            for check, u in [("bending", u_bend), ("shear", u_shear), ("support", u_support)]:
                if u > max_uls_utilization:
                    max_uls_utilization = u
                    governing_uls_check_name = check
                if u > 1.0:
                    passed_all = False
            
        elif comb.combination_type in [CombinationType.SLS_CHARACTERISTIC, CombinationType.SLS_QUASI_PERMANENT]:
            g_kN_m2 = sum(t.design_value_kN_per_m2 for t in comb.terms if t.action_type == ActionType.PERMANENT)
            q_kN_m2 = sum(t.design_value_kN_per_m2 for t in comb.terms if t.action_type != ActionType.PERMANENT)
            
            g_line = g_kN_m2 * spacing_m
            q_line = q_kN_m2 * spacing_m
            total_line = g_line + q_line
            
            # Use feminine solver for M deflection (global continuous model)
            if total_line > 0:
                fem_sls_output = _run_fem_analysis(
                    span_m=span_m,
                    supports=request.supports,
                    EI_Nmm2=geom.EI_ef_SLS,
                    line_loads=[
                        DistributedLoad(start_m=0.0, end_m=span_m, value_kN_per_m=-total_line, direction=DistributedLoadDirection.GLOBAL_Y)
                    ]
                )
                u_inst_M = fem_sls_output.summary.max_deflection_mm
            else:
                u_inst_M = 0.0
            
            # Shear deflection (analytical approximation w_V = qL^2 / (8GA)) - Note: this assumes single span nature for shear mode.
            u_inst_V = (total_line * (span_m * 1000)**2) / (8.0 * G_web * A_web) if A_web > 0 else 0.0
            
            u_inst = u_inst_M + u_inst_V
            
            if comb.combination_type == CombinationType.SLS_CHARACTERISTIC:
                capacity_inst = request.span.L_ef_mm / 300.0
                util_inst = u_inst / capacity_inst if capacity_inst > 0 else float('inf')
                
                combo_tag = comb.leading_action_id or "perm"
                sls_checks.append(KertoRipaCheckResult(
                    check=f"deflection_instantaneous_{combo_tag}", demand=u_inst, capacity=capacity_inst,
                    utilization=util_inst, unit="mm", passed=util_inst <= 1.0
                ))
                if util_inst > 1.0: passed_all = False
                
            elif comb.combination_type == CombinationType.SLS_QUASI_PERMANENT:
                # We can approximate final deflection for G and Q. The FEM gives combined. 
                # To be exact, we should run G and Q independently in FEM. 
                # Let's cleanly separate G and Q for exact k_def math:
                fem_sls_G = _run_fem_analysis(span_m, request.supports, geom.EI_ef_SLS, [DistributedLoad(start_m=0.0, end_m=span_m, value_kN_per_m=-g_line, direction=DistributedLoadDirection.GLOBAL_Y)]) if g_line > 0 else None
                fem_sls_Q = _run_fem_analysis(span_m, request.supports, geom.EI_ef_SLS, [DistributedLoad(start_m=0.0, end_m=span_m, value_kN_per_m=-q_line, direction=DistributedLoadDirection.GLOBAL_Y)]) if q_line > 0 else None
                
                u_inst_M_g = fem_sls_G.summary.max_deflection_mm if fem_sls_G else 0.0
                u_inst_V_g = (g_line * (span_m * 1000)**2) / (8.0 * G_web * A_web) if A_web > 0 else 0.0
                
                u_inst_M_q_psi = fem_sls_Q.summary.max_deflection_mm if fem_sls_Q else 0.0
                u_inst_V_q_psi = (q_line * (span_m * 1000)**2) / (8.0 * G_web * A_web) if A_web > 0 else 0.0
                
                u_fin = calculate_final_deflection(
                    u_inst_g_mm=(u_inst_M_g + u_inst_V_g), 
                    u_inst_q_mm=(u_inst_M_q_psi + u_inst_V_q_psi), 
                    k_def=k_def, 
                    psi_2=1.0 # Combinator provides quasi-permanent Q scaled by psi_2
                )
                
                capacity_fin = request.span.L_ef_mm / 200.0
                util_fin = u_fin / capacity_fin if capacity_fin > 0 else float('inf')
                
                combo_tag = comb.leading_action_id or "perm"
                sls_checks.append(KertoRipaCheckResult(
                    check=f"deflection_final_{combo_tag}", demand=u_fin, capacity=capacity_fin,
                    utilization=util_fin, unit="mm", passed=util_fin <= 1.0
                ))
                if util_fin > 1.0: passed_all = False

    if max_uls_utilization > 1.0:
        warnings.append(WarningMessage(code="ULS_FAILED", message="One or more ULS checks failed capacity limits."))
        
    # Inform user about shear deflection approx in warning
    if request.span.support_position != "end" or len(request.supports) > 2:
        warnings.append(WarningMessage(
            code="SHEAR_DEFLECTION_APPROX", 
            message="FEM used for bending deflections over continuous supports, but shear deflection uses a single-span analytical envelope approximation."
        ))

    summary = {
        "passed": passed_all,
        "governing_check": governing_uls_check_name,
        "max_uls_utilization": max_uls_utilization,
    }

    return KertoRipaCalculationResponse(
        summary=summary,
        geometry=geom_res,
        uls_checks=uls_checks,
        sls_checks=sls_checks,
        intermediate_values=intermediate,
        warnings=warnings
    )
