import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.schemas.kertoripa import (
    KertoRipaCalculationRequest,
    KertoRipaCrossSectionInput,
    KertoRipaSpanInput,
    KertoRipaDesignBasis,
    LoadDurationClass,
)
from app.schemas.fem import BeamSupport, SupportType
from app.schemas.actions import ProjectActionCatalog, ProjectAction, PermanentActionPattern, PermanentActionOrigin, ImposedActionPattern, ImposedLoadCategory, CombinationFactorSet
from app.schemas.floor_joist import ServiceClass, NationalAnnexProfile
from app.domain.kertoripa.calculator import calculate_kerto_ripa

def main():
    b_w = 45.0
    h_w = 225.0
    h_f1 = 25.0
    
    spacing = 585.0
    
    span = 5500.0  # mm
    span_m = 5.5   # m
    L_support = 100.0

    cs = KertoRipaCrossSectionInput(
        section_type="ribbed_top",
        element_width_mm=spacing * 2,
        n_ribs=2,
        b_w_mm=b_w,
        h_w_mm=h_w,
        h_f1_mm=h_f1,
        h_f2_mm=None
    )

    sp = KertoRipaSpanInput(
        L_ef_mm=span,
        L_support_mm=L_support,
        support_position="end"
    )
    
    supports = [
        BeamSupport(position_m=0.0, support_type=SupportType.PINNED),
        BeamSupport(position_m=span_m, support_type=SupportType.ROLLER),
    ]

    db = KertoRipaDesignBasis(
        service_class=ServiceClass.SC1,
        load_duration_class=LoadDurationClass.MEDIUM_TERM,
        national_annex_profile=NationalAnnexProfile.SPAIN_TIMBER_BUILDINGS
    )

    g = 0.9
    q = 2.5
    
    cat = ProjectActionCatalog(
        actions=[
            ProjectAction(
                id="G_test",
                pattern=PermanentActionPattern(
                    name="Dead load",
                    value_kN_per_m2=g,
                    origin=PermanentActionOrigin.SELF_WEIGHT,
                )
            ),
            ProjectAction(
                id="Q_test",
                pattern=ImposedActionPattern(
                    name="Live load",
                    value_kN_per_m2=q,
                    imposed_load_category=ImposedLoadCategory.A
                ),
                combination_factors=CombinationFactorSet(psi0=0.7, psi1=0.5, psi2=0.3)
            )
        ]
    )

    request = KertoRipaCalculationRequest(
        cross_section=cs,
        span=sp,
        supports=supports,
        design_basis=db,
        action_catalog=cat
    )

    res = calculate_kerto_ripa(request)
    
    print("=== KERTO-RIPA EXAMPLE B VALIDATION ===\n")
    
    tol = 0.5
    def check_val(name, actual, expected):
        diff = abs(actual - expected)
        status = "PASSED" if diff <= tol else "FAILED"
        print(f"[{status}] {name}:\n  Actual   = {actual:.2f}\n  Expected = {expected:.2f}\n  Diff     = {diff:.2f}\n")

    check_val("R_M,k (Bending capacity base) [kNm]", res.intermediate_values["bending_modes"]["R_M_k_governing"], 103.2)
    check_val("R_V,k (Shear capacity) [kN]", res.intermediate_values["shear_modes"]["R_V_k_governing"], 29.1)
    check_val("R_c,90,k (Support compression) [kN]", res.intermediate_values["support_modes"]["R_c_90_k_governing"], 37.2)
    
    u_inst_check = next((c for c in res.sls_checks if "deflection_instantaneous" in c.check), None)
    u_fin_check = next((c for c in res.sls_checks if "deflection_final" in c.check), None)
    
    check_val("w_inst (Instantaneous deflection) [mm]", u_inst_check.demand if u_inst_check else 0.0, 5.38)
    check_val("w_net_fin (Final deflection) [mm]", u_fin_check.demand if u_fin_check else 0.0, 6.95)
    
    print("\n--- INTERMEDIATE VALUES ---")
    print(f"EI_ef_ULS: {res.geometry.EI_ef_ULS_Nmm2:.2e}")
    print(f"EI_ef_SLS: {res.geometry.EI_ef_SLS_Nmm2:.2e}")
    print(f"a_2: {res.geometry.neutral_axis_a2_mm:.2f}")
    print(f"b_ef_top_ULS: {res.geometry.b_ef_ULS_top_mm:.2f}")
    print(f"b_ef_top_SLS: {res.geometry.b_ef_SLS_top_mm:.2f}")
    print("Bending Modes:", res.intermediate_values['bending_modes'])
    print("Shear Modes:", res.intermediate_values['shear_modes'])
    print("Support Modes:", res.intermediate_values['support_modes'])


if __name__ == '__main__':
    main()
