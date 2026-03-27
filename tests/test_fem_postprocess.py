from app.domain.fem import analyze_beam
from app.schemas.fem import BeamAnalysisRequest, ResultDiagramType


def build_request() -> BeamAnalysisRequest:
    return BeamAnalysisRequest.model_validate(
        {
            "span": {
                "length_m": 4.0,
                "element_count": 4,
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
                }
            ],
        }
    )


def test_analyze_beam_returns_nodes_elements_diagrams_and_reactions():
    response = analyze_beam(build_request())

    assert response.summary.total_nodes == 5
    assert response.summary.total_elements == 4
    assert len(response.nodes) == 5
    assert len(response.elements) == 4
    assert len(response.reactions) == 2
    assert {diagram.diagram_type for diagram in response.diagrams} == {
        ResultDiagramType.DEFLECTION,
        ResultDiagramType.ROTATION,
        ResultDiagramType.SHEAR,
        ResultDiagramType.MOMENT,
    }


def test_analyze_beam_summary_matches_reference_values():
    response = analyze_beam(build_request())

    assert round(response.summary.max_deflection_mm, 3) == 11.544
    assert response.summary.max_deflection_position_m == 2.0
    assert round(response.summary.max_moment_kNm, 3) == 3.2
    assert round(response.summary.max_shear_kN, 3) == 3.2


def test_analyze_beam_reactions_match_simply_supported_reference_case():
    response = analyze_beam(build_request())

    assert round(response.reactions[0].vertical_reaction_kN, 3) == 3.2
    assert round(response.reactions[1].vertical_reaction_kN, 3) == 3.2


def test_analyze_beam_diagrams_include_midspan_deflection_and_end_moments():
    response = analyze_beam(build_request())
    deflection_diagram = next(
        diagram for diagram in response.diagrams if diagram.diagram_type == ResultDiagramType.DEFLECTION
    )
    moment_diagram = next(
        diagram for diagram in response.diagrams if diagram.diagram_type == ResultDiagramType.MOMENT
    )

    midspan_point = next(point for point in deflection_diagram.points if point.x_m == 2.0)

    assert round(midspan_point.value, 3) == -11.544
    assert round(moment_diagram.points[0].value, 3) == 0.0
    assert round(moment_diagram.points[-1].value, 3) == 0.0


def test_analyze_beam_shear_diagram_keeps_support_jumps():
    response = analyze_beam(build_request())
    shear_diagram = next(
        diagram for diagram in response.diagrams if diagram.diagram_type == ResultDiagramType.SHEAR
    )

    start_points = [point for point in shear_diagram.points if point.x_m == 0.0]
    end_points = [point for point in shear_diagram.points if point.x_m == 4.0]

    assert [round(point.value, 3) for point in start_points] == [0.0, 3.2]
    assert [round(point.value, 3) for point in end_points] == [-3.2, 0.0]
