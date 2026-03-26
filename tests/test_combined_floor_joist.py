from app.domain.calculator import calculate_floor_joist_with_combinations
from app.schemas.floor_joist import FloorJoistCombinationCalculationRequest


def build_request() -> FloorJoistCombinationCalculationRequest:
    return FloorJoistCombinationCalculationRequest.model_validate(
        {
            "project_name": "Combined load case",
            "geometry": {
                "span_m": 4.0,
                "spacing_m": 0.4,
                "width_mm": 63.0,
                "depth_mm": 200.0,
            },
            "timber": {
                "grade": "C24",
                "modulus_of_elasticity_mpa": 11000.0,
                "allowable_bending_stress_mpa": 11.0,
                "allowable_shear_stress_mpa": 1.2,
            },
            "supports": [
                {"position_m": 0.0, "support_type": "pinned"},
                {"position_m": 4.0, "support_type": "roller"},
            ],
            "criteria": {
                "design_standard": "concept-v1",
                "max_deflection_ratio": 300.0,
                "national_annex_profile": "spain_timber_buildings",
                "service_class": "service_class_1",
                "active_deflection_criterion": "ordinary_elements",
            },
            "action_catalog": {
                "actions": [
                    {
                        "id": "g_self",
                        "pattern": {
                            "action_type": "permanent",
                            "name": "Self weight",
                            "origin": "self_weight",
                            "value_kN_per_m2": 0.8,
                        },
                    },
                    {
                        "id": "g_finishes",
                        "pattern": {
                            "action_type": "permanent",
                            "name": "Finishes",
                            "origin": "non_structural",
                            "value_kN_per_m2": 0.7,
                        },
                    },
                    {
                        "id": "q_imposed",
                        "pattern": {
                            "action_type": "imposed",
                            "name": "Residential imposed load",
                            "imposed_load_category": "A",
                            "value_kN_per_m2": 2.0,
                        },
                        "combination_factors": {
                            "psi0": 0.7,
                            "psi1": 0.5,
                            "psi2": 0.3,
                        },
                    },
                    {
                        "id": "q_snow",
                        "pattern": {
                            "action_type": "snow",
                            "name": "Snow",
                            "value_kN_per_m2": 0.8,
                        },
                        "combination_factors": {
                            "psi0": 0.5,
                            "psi1": 0.2,
                            "psi2": 0.0,
                        },
                    },
                ]
            },
        }
    )


def test_combined_calculation_returns_one_case_per_generated_combination():
    response = calculate_floor_joist_with_combinations(build_request())

    assert len(response.uls_combinations) == 2
    assert len(response.sls_combinations) == 3
    assert response.summary["uls_passed"] is True
    assert response.uls_summary.governing_combination_type == "uls_fundamental"
    assert response.uls_summary.governing_leading_action_id == "q_imposed"
    assert response.sls_summary.governing_combination_type in {"sls_characteristic", "sls_quasi_permanent"}
    assert response.national_annex_notes


def test_combined_calculation_produces_numeric_results_for_each_combination():
    response = calculate_floor_joist_with_combinations(build_request())
    first_case = response.uls_combinations[0]
    first_sls_case = response.sls_combinations[0]

    assert first_case.results.line_load_kN_per_m > 0
    assert len(first_case.checks) == 2
    assert first_case.combination.total_design_value_kN_per_m2 > 0
    assert first_case.summary.governing_check in {"bending", "shear", "deflection"}
    assert len(first_sls_case.checks) >= 1
    assert first_sls_case.summary.governing_check in {
        "deflection_active",
        "deflection_instantaneous",
        "deflection_final",
    }
