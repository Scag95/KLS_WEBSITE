from pydantic import ValidationError

from app.schemas.fem import BeamAnalysisRequest, BeamAnalysisResponse


def build_request() -> BeamAnalysisRequest:
    return BeamAnalysisRequest.model_validate(
        {
            "project_name": "Simple beam",
            "span": {
                "length_m": 4.0,
                "element_count": 16,
            },
            "material": {
                "modulus_of_elasticity_mpa": 11000.0,
            },
            "section": {
                "width_mm": 63.0,
                "depth_mm": 200.0,
            },
            "supports": [
                {"position_m": 0.0, "support_type": "pinned"},
                {"position_m": 4.0, "support_type": "roller"},
            ],
            "loads": [
                {
                    "load_type": "distributed",
                    "start_m": 0.0,
                    "end_m": 4.0,
                    "value_kN_per_m": -1.6,
                },
                {
                    "load_type": "point",
                    "position_m": 2.0,
                    "value_kN": -3.0,
                },
            ],
        }
    )


def test_beam_analysis_request_accepts_basic_simply_supported_beam():
    request = build_request()

    assert request.span.length_m == 4.0
    assert request.span.element_count == 16
    assert request.section.inertia_mm4 == 42000000.0
    assert len(request.loads) == 2


def test_beam_analysis_request_rejects_loads_outside_span():
    try:
        BeamAnalysisRequest.model_validate(
            {
                "span": {"length_m": 4.0, "element_count": 10},
                "material": {"modulus_of_elasticity_mpa": 11000.0},
                "section": {"width_mm": 63.0, "depth_mm": 200.0},
                "supports": [
                    {"position_m": 0.0, "support_type": "pinned"},
                    {"position_m": 4.0, "support_type": "roller"},
                ],
                "loads": [
                    {
                        "load_type": "point",
                        "position_m": 4.5,
                        "value_kN": -2.0,
                    }
                ],
            }
        )
    except ValidationError as error:
        assert "beyond the beam span" in str(error)
    else:
        raise AssertionError("Loads outside the span must be rejected.")


def test_beam_analysis_request_requires_stable_support_configuration():
    try:
        BeamAnalysisRequest.model_validate(
            {
                "span": {"length_m": 4.0, "element_count": 10},
                "material": {"modulus_of_elasticity_mpa": 11000.0},
                "section": {"width_mm": 63.0, "depth_mm": 200.0},
                "supports": [
                    {"position_m": 0.0, "support_type": "roller"},
                ],
                "loads": [],
            }
        )
    except ValidationError as error:
        assert "stable beam model" in str(error)
    else:
        raise AssertionError("A beam model without enough restraints must be rejected.")


def test_beam_analysis_response_supports_diagram_payload():
    response = BeamAnalysisResponse.model_validate(
        {
            "summary": {
                "total_nodes": 3,
                "total_elements": 2,
                "max_deflection_mm": 11.5,
                "max_deflection_position_m": 2.0,
                "max_moment_kNm": 3.2,
                "max_shear_kN": 3.2,
            },
            "nodes": [
                {"node_id": 0, "x_m": 0.0, "vertical_displacement_mm": 0.0, "rotation_rad": 0.001},
                {"node_id": 1, "x_m": 2.0, "vertical_displacement_mm": -11.5, "rotation_rad": 0.0},
                {"node_id": 2, "x_m": 4.0, "vertical_displacement_mm": 0.0, "rotation_rad": -0.001},
            ],
            "elements": [
                {"element_id": 0, "start_x_m": 0.0, "end_x_m": 2.0, "length_m": 2.0},
                {"element_id": 1, "start_x_m": 2.0, "end_x_m": 4.0, "length_m": 2.0},
            ],
            "diagrams": [
                {
                    "diagram_type": "moment",
                    "unit": "kNm",
                    "points": [
                        {"x_m": 0.0, "value": 0.0},
                        {"x_m": 2.0, "value": 3.2},
                        {"x_m": 4.0, "value": 0.0},
                    ],
                }
            ],
            "reactions": [
                {"position_m": 0.0, "vertical_reaction_kN": 3.2},
                {"position_m": 4.0, "vertical_reaction_kN": 3.2},
            ],
        }
    )

    assert response.summary.total_elements == 2
    assert response.diagrams[0].diagram_type == "moment"
    assert response.reactions[0].vertical_reaction_kN == 3.2
