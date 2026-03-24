from app.domain.fem import (
    assemble_global_load_vector,
    assemble_global_stiffness,
    generate_uniform_beam_mesh,
    reaction_vector,
    restrained_dof_indices,
    solve_beam_displacements,
)
from app.schemas.fem import BeamAnalysisRequest


def build_simply_supported_uniform_load_request() -> BeamAnalysisRequest:
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


def test_assemble_global_load_vector_for_uniform_load_matches_total_applied_load():
    request = build_simply_supported_uniform_load_request()
    mesh = generate_uniform_beam_mesh(request)

    global_load = assemble_global_load_vector(request, mesh)
    vertical_components = global_load[0::2]

    assert round(sum(vertical_components), 6) == -6400.0


def test_restrained_dofs_match_pinned_and_roller_supports():
    request = build_simply_supported_uniform_load_request()
    mesh = generate_uniform_beam_mesh(request)

    assert restrained_dof_indices(request, mesh) == [0, 8]


def test_solver_returns_zero_displacements_at_supported_vertical_dofs():
    request = build_simply_supported_uniform_load_request()
    mesh = generate_uniform_beam_mesh(request)
    global_stiffness = assemble_global_stiffness(mesh, request.material, request.section)
    global_load = assemble_global_load_vector(request, mesh)

    displacements = solve_beam_displacements(request, mesh, global_stiffness, global_load)

    assert displacements[0] == 0.0
    assert displacements[8] == 0.0
    assert displacements[4] < 0.0


def test_reactions_balance_uniform_load():
    request = build_simply_supported_uniform_load_request()
    mesh = generate_uniform_beam_mesh(request)
    global_stiffness = assemble_global_stiffness(mesh, request.material, request.section)
    global_load = assemble_global_load_vector(request, mesh)
    displacements = solve_beam_displacements(request, mesh, global_stiffness, global_load)

    reactions = reaction_vector(global_stiffness, displacements, global_load)
    vertical_reactions = [reactions[index] for index in restrained_dof_indices(request, mesh)]

    assert round(sum(vertical_reactions), 6) == 6400.0
    assert round(vertical_reactions[0], 6) == 3200.0
    assert round(vertical_reactions[1], 6) == 3200.0


def test_solver_midspan_deflection_is_close_to_closed_form_solution():
    request = build_simply_supported_uniform_load_request()
    mesh = generate_uniform_beam_mesh(request)
    global_stiffness = assemble_global_stiffness(mesh, request.material, request.section)
    global_load = assemble_global_load_vector(request, mesh)

    displacements = solve_beam_displacements(request, mesh, global_stiffness, global_load)
    midspan_deflection_mm = displacements[4]

    assert round(midspan_deflection_mm, 3) == -11.544
