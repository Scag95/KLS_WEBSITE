from app.domain.fem import (
    assemble_global_stiffness,
    beam_element_stiffness_matrix,
    element_dof_indices,
    generate_uniform_beam_mesh,
)
from app.schemas.fem import BeamAnalysisRequest


def build_request(element_count: int = 4) -> BeamAnalysisRequest:
    return BeamAnalysisRequest.model_validate(
        {
            "span": {
                "length_m": 4.0,
                "element_count": element_count,
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
            "loads": [],
        }
    )


def test_generate_uniform_beam_mesh_creates_expected_nodes_and_elements():
    mesh = generate_uniform_beam_mesh(build_request(element_count=4))

    assert len(mesh.nodes) == 5
    assert len(mesh.elements) == 4
    assert [node.x_m for node in mesh.nodes] == [0.0, 1.0, 2.0, 3.0, 4.0]
    assert mesh.elements[0].length_m == 1.0
    assert mesh.elements[-1].start_node_id == 3
    assert mesh.elements[-1].end_node_id == 4


def test_generate_uniform_beam_mesh_places_nodes_at_support_and_point_load_positions():
    request = BeamAnalysisRequest.model_validate(
        {
            "span": {
                "length_m": 4.0,
                "element_count": 8,
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
                {"position_m": 1.5, "support_type": "roller"},
                {"position_m": 4.0, "support_type": "roller"},
            ],
            "loads": [
                {
                    "load_type": "point",
                    "position_m": 2.25,
                    "value_kN": -3.0,
                }
            ],
        }
    )

    mesh = generate_uniform_beam_mesh(request)
    node_positions = [round(node.x_m, 6) for node in mesh.nodes]

    assert 1.5 in node_positions
    assert 2.25 in node_positions
    assert 4.0 in node_positions


def test_generate_uniform_beam_mesh_places_nodes_at_distributed_load_boundaries():
    request = BeamAnalysisRequest.model_validate(
        {
            "span": {
                "length_m": 5.0,
                "element_count": 10,
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
                {"position_m": 5.0, "support_type": "roller"},
            ],
            "loads": [
                {
                    "load_type": "distributed",
                    "start_m": 1.0,
                    "end_m": 3.5,
                    "value_kN_per_m": -1.2,
                }
            ],
        }
    )

    mesh = generate_uniform_beam_mesh(request)
    node_positions = [round(node.x_m, 6) for node in mesh.nodes]

    assert 1.0 in node_positions
    assert 3.5 in node_positions


def test_beam_element_stiffness_matrix_matches_euler_bernoulli_form():
    request = build_request(element_count=2)
    matrix = beam_element_stiffness_matrix(
        request.material,
        request.section,
        length_m=2.0,
    )

    e = request.material.modulus_of_elasticity_mpa
    i = request.section.inertia_mm4
    l_mm = 2000.0
    factor = (e * i) / (l_mm**3)

    assert matrix[0][0] == 12.0 * factor
    assert matrix[0][1] == 6.0 * l_mm * factor
    assert matrix[1][1] == 4.0 * l_mm**2 * factor
    assert matrix[0][2] == -12.0 * factor
    assert matrix[0][0] == matrix[2][2]
    assert matrix[0][1] == matrix[1][0]


def test_element_dof_indices_use_two_dofs_per_node():
    mesh = generate_uniform_beam_mesh(build_request(element_count=2))

    assert element_dof_indices(mesh.elements[0]) == [0, 1, 2, 3]
    assert element_dof_indices(mesh.elements[1]) == [2, 3, 4, 5]


def test_assemble_global_stiffness_builds_expected_matrix_size_and_overlap():
    request = build_request(element_count=2)
    mesh = generate_uniform_beam_mesh(request)
    global_matrix = assemble_global_stiffness(mesh, request.material, request.section)
    local_matrix = beam_element_stiffness_matrix(request.material, request.section, length_m=2.0)

    assert len(global_matrix) == 6
    assert all(len(row) == 6 for row in global_matrix)
    assert global_matrix[0][0] == local_matrix[0][0]
    assert global_matrix[4][4] == local_matrix[2][2]
    assert global_matrix[2][2] == local_matrix[2][2] + local_matrix[0][0]
    assert global_matrix[2][3] == local_matrix[2][3] + local_matrix[0][1]
