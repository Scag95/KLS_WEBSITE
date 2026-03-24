from app.domain.calculator import calculate_floor_joist
from app.schemas.floor_joist import FloorJoistCalculationRequest


def build_request(**overrides) -> FloorJoistCalculationRequest:
    payload = {
        "project_name": "Reference case",
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
        "loads": {
            "dead_load_kN_per_m2": 1.5,
            "imposed_load_kN_per_m2": 2.0,
            "additional_dead_load_kN_per_m2": 0.5,
        },
        "criteria": {
            "design_standard": "concept-v1",
            "max_deflection_ratio": 300.0,
        },
    }
    payload.update(overrides)
    return FloorJoistCalculationRequest.model_validate(payload)


def test_calculator_returns_expected_reference_values():
    response = calculate_floor_joist(build_request())

    assert response.summary.passed is True
    assert response.summary.governing_check == "deflection"
    assert response.results.line_load_kN_per_m == 1.6
    assert round(response.results.max_moment_kNm, 3) == 3.2
    assert round(response.results.max_shear_kN, 3) == 3.2
    assert round(response.results.bending_stress_mpa, 3) == 7.619
    assert round(response.results.shear_stress_mpa, 3) == 0.381
    assert round(response.results.deflection_mm, 3) == 11.544


def test_calculator_fails_when_section_is_too_small():
    request = build_request(geometry={"span_m": 5.0, "spacing_m": 0.6, "width_mm": 45.0, "depth_mm": 145.0})

    response = calculate_floor_joist(request)

    assert response.summary.passed is False
    assert response.summary.governing_check == "deflection"
    assert any(check.check == "bending" and check.passed is False for check in response.checks)
    assert any(check.check == "deflection" and check.passed is False for check in response.checks)
    assert any(warning.code == "SPAN_DEPTH_RATIO_HIGH" for warning in response.warnings)


def test_calculator_warns_when_imposed_load_is_zero():
    request = build_request(loads={"dead_load_kN_per_m2": 1.5, "imposed_load_kN_per_m2": 0.0, "additional_dead_load_kN_per_m2": 0.0})

    response = calculate_floor_joist(request)

    assert any(warning.code == "ZERO_IMPOSED_LOAD" for warning in response.warnings)
