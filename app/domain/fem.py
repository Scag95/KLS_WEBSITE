from __future__ import annotations

from dataclasses import dataclass

from app.schemas.fem import (
    BeamAnalysisResponse,
    BeamAnalysisRequest,
    BeamAnalysisSummary,
    BeamMaterial,
    BeamSection,
    DiagramPoint,
    DiagramSeries,
    DistributedLoad,
    ElementResult,
    NodeResult,
    PointLoad,
    PointMoment,
    ResultDiagramType,
    SupportReaction,
    SupportType,
)


MM_PER_M = 1000.0
DOF_PER_NODE = 2
POSITION_TOLERANCE_M = 1e-9


@dataclass(frozen=True)
class FEMNode:
    id: int
    x_m: float


@dataclass(frozen=True)
class FEMElement:
    id: int
    start_node_id: int
    end_node_id: int
    length_m: float


@dataclass(frozen=True)
class FEMMesh:
    nodes: list[FEMNode]
    elements: list[FEMElement]


def _event_positions(request: BeamAnalysisRequest) -> list[float]:
    positions = {0.0, request.span.length_m}

    for support in request.supports:
        positions.add(support.position_m)

    for load in request.loads:
        if isinstance(load, DistributedLoad):
            positions.add(load.start_m)
            positions.add(load.end_m)
        elif isinstance(load, (PointLoad, PointMoment)):
            positions.add(load.position_m)

    return sorted(positions)


def _subdivision_counts(segment_lengths: list[float], target_total_elements: int) -> list[int]:
    segment_count = len(segment_lengths)
    if segment_count == 0:
        return []

    minimum_counts = [1 for _ in segment_lengths]
    remaining = max(target_total_elements - segment_count, 0)
    total_length = sum(segment_lengths)

    if remaining == 0 or total_length == 0:
        return minimum_counts

    raw_allocations = [(length / total_length) * remaining for length in segment_lengths]
    integer_parts = [int(allocation) for allocation in raw_allocations]
    counts = [base + extra for base, extra in zip(minimum_counts, integer_parts, strict=True)]
    assigned = sum(integer_parts)

    remainders = sorted(
        (
            (raw_allocations[index] - integer_parts[index], index)
            for index in range(segment_count)
        ),
        reverse=True,
    )
    for _, index in remainders[: remaining - assigned]:
        counts[index] += 1

    return counts


def generate_uniform_beam_mesh(request: BeamAnalysisRequest) -> FEMMesh:
    event_positions = _event_positions(request)
    segment_lengths = [
        event_positions[index + 1] - event_positions[index]
        for index in range(len(event_positions) - 1)
    ]
    subdivision_counts = _subdivision_counts(segment_lengths, request.span.element_count)

    node_positions: list[float] = [event_positions[0]]
    for segment_index, segment_length in enumerate(segment_lengths):
        start_position = event_positions[segment_index]
        subdivisions = subdivision_counts[segment_index]
        step = segment_length / subdivisions
        for step_index in range(1, subdivisions + 1):
            node_positions.append(start_position + step * step_index)

    deduped_positions: list[float] = []
    for position in node_positions:
        if not deduped_positions or abs(position - deduped_positions[-1]) > POSITION_TOLERANCE_M:
            deduped_positions.append(position)

    nodes = [
        FEMNode(id=node_id, x_m=position)
        for node_id, position in enumerate(deduped_positions)
    ]
    elements = [
        FEMElement(
            id=element_id,
            start_node_id=element_id,
            end_node_id=element_id + 1,
            length_m=nodes[element_id + 1].x_m - nodes[element_id].x_m,
        )
        for element_id in range(len(nodes) - 1)
    ]
    return FEMMesh(nodes=nodes, elements=elements)


def beam_element_stiffness_matrix(
    material: BeamMaterial,
    section: BeamSection,
    length_m: float,
) -> list[list[float]]:
    length_mm = length_m * MM_PER_M
    stiffness_factor = (material.modulus_of_elasticity_mpa * section.inertia_mm4) / (length_mm**3)
    l = length_mm

    template = [
        [12.0, 6.0 * l, -12.0, 6.0 * l],
        [6.0 * l, 4.0 * l**2, -6.0 * l, 2.0 * l**2],
        [-12.0, -6.0 * l, 12.0, -6.0 * l],
        [6.0 * l, 2.0 * l**2, -6.0 * l, 4.0 * l**2],
    ]
    return [
        [stiffness_factor * coefficient for coefficient in row]
        for row in template
    ]


def element_dof_indices(element: FEMElement) -> list[int]:
    start = element.start_node_id * DOF_PER_NODE
    end = element.end_node_id * DOF_PER_NODE
    return [start, start + 1, end, end + 1]


def assemble_global_stiffness(
    mesh: FEMMesh,
    material: BeamMaterial,
    section: BeamSection,
) -> list[list[float]]:
    total_dofs = len(mesh.nodes) * DOF_PER_NODE
    global_matrix = [[0.0 for _ in range(total_dofs)] for _ in range(total_dofs)]

    for element in mesh.elements:
        local_matrix = beam_element_stiffness_matrix(material, section, element.length_m)
        dof_indices = element_dof_indices(element)

        for local_i, global_i in enumerate(dof_indices):
            for local_j, global_j in enumerate(dof_indices):
                global_matrix[global_i][global_j] += local_matrix[local_i][local_j]

    return global_matrix


def _find_node_id_at_position(mesh: FEMMesh, position_m: float) -> int:
    for node in mesh.nodes:
        if abs(node.x_m - position_m) <= POSITION_TOLERANCE_M:
            return node.id
    raise ValueError(
        f"Position {position_m} m does not match a mesh node. "
        "In this first solver version, point loads, moments, and supports must be placed on nodes."
    )


def _find_element_ids_in_range(mesh: FEMMesh, start_m: float, end_m: float) -> list[int]:
    element_ids: list[int] = []
    for element in mesh.elements:
        start_x = mesh.nodes[element.start_node_id].x_m
        end_x = mesh.nodes[element.end_node_id].x_m
        if abs(start_x - start_m) <= POSITION_TOLERANCE_M and abs(end_x - end_m) <= POSITION_TOLERANCE_M:
            return [element.id]
        if start_x >= start_m - POSITION_TOLERANCE_M and end_x <= end_m + POSITION_TOLERANCE_M:
            element_ids.append(element.id)

    covered_length = sum(mesh.elements[element_id].length_m for element_id in element_ids)
    if abs(covered_length - (end_m - start_m)) > POSITION_TOLERANCE_M:
        raise ValueError(
            "Distributed loads must align with mesh element boundaries in this first solver version."
        )
    return element_ids


def _uniform_distributed_element_load_vector(length_m: float, value_kN_per_m: float) -> list[float]:
    length_mm = length_m * MM_PER_M
    load_n_per_mm = value_kN_per_m
    return [
        load_n_per_mm * length_mm / 2.0,
        load_n_per_mm * length_mm**2 / 12.0,
        load_n_per_mm * length_mm / 2.0,
        -load_n_per_mm * length_mm**2 / 12.0,
    ]


def assemble_global_load_vector(request: BeamAnalysisRequest, mesh: FEMMesh) -> list[float]:
    total_dofs = len(mesh.nodes) * DOF_PER_NODE
    global_vector = [0.0 for _ in range(total_dofs)]

    for load in request.loads:
        if isinstance(load, DistributedLoad):
            for element_id in _find_element_ids_in_range(mesh, load.start_m, load.end_m):
                element = mesh.elements[element_id]
                dof_indices = element_dof_indices(element)
                local_vector = _uniform_distributed_element_load_vector(
                    element.length_m,
                    load.value_kN_per_m,
                )
                for local_i, global_i in enumerate(dof_indices):
                    global_vector[global_i] += local_vector[local_i]
        elif isinstance(load, PointLoad):
            node_id = _find_node_id_at_position(mesh, load.position_m)
            global_vector[node_id * DOF_PER_NODE] += load.value_kN * 1000.0
        elif isinstance(load, PointMoment):
            node_id = _find_node_id_at_position(mesh, load.position_m)
            global_vector[node_id * DOF_PER_NODE + 1] += load.value_kNm * 1_000_000.0

    return global_vector


def restrained_dof_indices(request: BeamAnalysisRequest, mesh: FEMMesh) -> list[int]:
    restrained: list[int] = []
    for support in request.supports:
        node_id = _find_node_id_at_position(mesh, support.position_m)
        displacement_dof = node_id * DOF_PER_NODE
        rotation_dof = displacement_dof + 1

        if support.support_type in {SupportType.PINNED, SupportType.ROLLER, SupportType.FIXED}:
            restrained.append(displacement_dof)
        if support.support_type == SupportType.FIXED:
            restrained.append(rotation_dof)

    return sorted(set(restrained))


def free_dof_indices(total_dofs: int, restrained_dofs: list[int]) -> list[int]:
    restrained = set(restrained_dofs)
    return [dof for dof in range(total_dofs) if dof not in restrained]


def submatrix(matrix: list[list[float]], row_indices: list[int], col_indices: list[int]) -> list[list[float]]:
    return [[matrix[row][col] for col in col_indices] for row in row_indices]


def subvect(vector: list[float], indices: list[int]) -> list[float]:
    return [vector[index] for index in indices]


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector, strict=True)]

    for pivot_index in range(size):
        pivot_row = max(range(pivot_index, size), key=lambda row: abs(augmented[row][pivot_index]))
        if abs(augmented[pivot_row][pivot_index]) < 1e-12:
            raise ValueError("Global stiffness matrix is singular. Check supports and mesh.")
        augmented[pivot_index], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_index]

        pivot_value = augmented[pivot_index][pivot_index]
        for column_index in range(pivot_index, size + 1):
            augmented[pivot_index][column_index] /= pivot_value

        for row_index in range(pivot_index + 1, size):
            factor = augmented[row_index][pivot_index]
            for column_index in range(pivot_index, size + 1):
                augmented[row_index][column_index] -= factor * augmented[pivot_index][column_index]

    solution = [0.0 for _ in range(size)]
    for row_index in range(size - 1, -1, -1):
        solution[row_index] = augmented[row_index][size] - sum(
            augmented[row_index][column_index] * solution[column_index]
            for column_index in range(row_index + 1, size)
        )
    return solution


def expand_displacements(total_dofs: int, free_dofs: list[int], reduced_solution: list[float]) -> list[float]:
    full_solution = [0.0 for _ in range(total_dofs)]
    for dof, value in zip(free_dofs, reduced_solution, strict=True):
        full_solution[dof] = value
    return full_solution


def solve_beam_displacements(
    request: BeamAnalysisRequest,
    mesh: FEMMesh,
    global_stiffness: list[list[float]],
    global_load: list[float],
) -> list[float]:
    total_dofs = len(mesh.nodes) * DOF_PER_NODE
    restrained_dofs = restrained_dof_indices(request, mesh)
    free_dofs = free_dof_indices(total_dofs, restrained_dofs)

    reduced_stiffness = submatrix(global_stiffness, free_dofs, free_dofs)
    reduced_load = subvect(global_load, free_dofs)
    reduced_solution = solve_linear_system(reduced_stiffness, reduced_load)
    return expand_displacements(total_dofs, free_dofs, reduced_solution)


def multiply_matrix_vector(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [
        sum(row[column_index] * vector[column_index] for column_index in range(len(vector)))
        for row in matrix
    ]


def reaction_vector(
    global_stiffness: list[list[float]],
    displacements: list[float],
    global_load: list[float],
) -> list[float]:
    stiffness_times_displacements = multiply_matrix_vector(global_stiffness, displacements)
    return [
        stiffness_times_displacements[index] - global_load[index]
        for index in range(len(global_load))
    ]


def _element_displacement_vector(element: FEMElement, global_displacements: list[float]) -> list[float]:
    dof_indices = element_dof_indices(element)
    return [global_displacements[index] for index in dof_indices]


def _element_applied_load_vector(
    request: BeamAnalysisRequest,
    mesh: FEMMesh,
    element: FEMElement,
) -> list[float]:
    local_vector = [0.0, 0.0, 0.0, 0.0]
    element_start = mesh.nodes[element.start_node_id].x_m
    element_end = mesh.nodes[element.end_node_id].x_m

    for load in request.loads:
        if isinstance(load, DistributedLoad):
            if abs(load.start_m - element_start) <= POSITION_TOLERANCE_M and abs(load.end_m - element_end) <= POSITION_TOLERANCE_M:
                equivalent = _uniform_distributed_element_load_vector(element.length_m, load.value_kN_per_m)
                local_vector = [value + addition for value, addition in zip(local_vector, equivalent, strict=True)]
        elif isinstance(load, PointLoad):
            if abs(load.position_m - element_start) <= POSITION_TOLERANCE_M:
                local_vector[0] += load.value_kN * 1000.0
            if abs(load.position_m - element_end) <= POSITION_TOLERANCE_M:
                local_vector[2] += load.value_kN * 1000.0
        elif isinstance(load, PointMoment):
            if abs(load.position_m - element_start) <= POSITION_TOLERANCE_M:
                local_vector[1] += load.value_kNm * 1_000_000.0
            if abs(load.position_m - element_end) <= POSITION_TOLERANCE_M:
                local_vector[3] += load.value_kNm * 1_000_000.0

    return local_vector


def _element_uniform_line_load_kN_per_m(
    request: BeamAnalysisRequest,
    mesh: FEMMesh,
    element: FEMElement,
) -> float:
    element_start = mesh.nodes[element.start_node_id].x_m
    element_end = mesh.nodes[element.end_node_id].x_m
    total = 0.0

    for load in request.loads:
        if isinstance(load, DistributedLoad):
            if load.start_m <= element_start + POSITION_TOLERANCE_M and load.end_m >= element_end - POSITION_TOLERANCE_M:
                total += load.value_kN_per_m

    return total


def element_end_force_vector(
    request: BeamAnalysisRequest,
    mesh: FEMMesh,
    element: FEMElement,
    material: BeamMaterial,
    section: BeamSection,
    global_displacements: list[float],
) -> list[float]:
    local_stiffness = beam_element_stiffness_matrix(material, section, element.length_m)
    local_displacements = _element_displacement_vector(element, global_displacements)
    resisting = multiply_matrix_vector(local_stiffness, local_displacements)
    applied = _element_applied_load_vector(request, mesh, element)
    return [resisting[index] - applied[index] for index in range(4)]


def build_node_results(mesh: FEMMesh, displacements: list[float]) -> list[NodeResult]:
    return [
        NodeResult(
            node_id=node.id,
            x_m=node.x_m,
            vertical_displacement_mm=displacements[node.id * DOF_PER_NODE],
            rotation_rad=displacements[node.id * DOF_PER_NODE + 1],
        )
        for node in mesh.nodes
    ]


def build_element_results(mesh: FEMMesh) -> list[ElementResult]:
    return [
        ElementResult(
            element_id=element.id,
            start_x_m=mesh.nodes[element.start_node_id].x_m,
            end_x_m=mesh.nodes[element.end_node_id].x_m,
            length_m=element.length_m,
        )
        for element in mesh.elements
    ]


def build_reaction_results(
    request: BeamAnalysisRequest,
    mesh: FEMMesh,
    reactions: list[float],
) -> list[SupportReaction]:
    result: list[SupportReaction] = []
    for support in request.supports:
        node_id = _find_node_id_at_position(mesh, support.position_m)
        displacement_dof = node_id * DOF_PER_NODE
        rotation_dof = displacement_dof + 1
        moment_reaction = reactions[rotation_dof] / 1_000_000.0 if support.support_type == SupportType.FIXED else None
        result.append(
            SupportReaction(
                position_m=support.position_m,
                vertical_reaction_kN=reactions[displacement_dof] / 1000.0,
                moment_reaction_kNm=moment_reaction,
            )
        )
    return result


def build_diagram_series(
    request: BeamAnalysisRequest,
    mesh: FEMMesh,
    material: BeamMaterial,
    section: BeamSection,
    displacements: list[float],
) -> list[DiagramSeries]:
    deflection_points = [
        DiagramPoint(
            x_m=node.x_m,
            value=displacements[node.id * DOF_PER_NODE],
        )
        for node in mesh.nodes
    ]
    rotation_points = [
        DiagramPoint(
            x_m=node.x_m,
            value=displacements[node.id * DOF_PER_NODE + 1],
        )
        for node in mesh.nodes
    ]

    nodal_vertical_forces_kN = {node.id: 0.0 for node in mesh.nodes}
    nodal_moments_kNm = {node.id: 0.0 for node in mesh.nodes}

    for load in request.loads:
        if isinstance(load, PointLoad):
            node_id = _find_node_id_at_position(mesh, load.position_m)
            nodal_vertical_forces_kN[node_id] += load.value_kN
        elif isinstance(load, PointMoment):
            node_id = _find_node_id_at_position(mesh, load.position_m)
            nodal_moments_kNm[node_id] += load.value_kNm

    shear_points: list[DiagramPoint] = []
    moment_points: list[DiagramPoint] = []
    current_shear_kN = 0.0
    current_moment_kNm = 0.0

    reactions_by_node = {node.id: 0.0 for node in mesh.nodes}
    for reaction in build_reaction_results(request, mesh, reaction_vector(assemble_global_stiffness(mesh, material, section), displacements, assemble_global_load_vector(request, mesh))):
        node_id = _find_node_id_at_position(mesh, reaction.position_m)
        reactions_by_node[node_id] += reaction.vertical_reaction_kN

    for node_index, node in enumerate(mesh.nodes):
        current_shear_kN += reactions_by_node[node.id]
        current_shear_kN += nodal_vertical_forces_kN[node.id]
        current_moment_kNm += nodal_moments_kNm[node.id]

        shear_points.append(DiagramPoint(x_m=node.x_m, value=current_shear_kN))
        moment_points.append(DiagramPoint(x_m=node.x_m, value=current_moment_kNm))

        if node_index == len(mesh.nodes) - 1:
            continue

        element = mesh.elements[node_index]
        line_load_kN_per_m = _element_uniform_line_load_kN_per_m(request, mesh, element)
        element_length_m = element.length_m
        current_moment_kNm += current_shear_kN * element_length_m + line_load_kN_per_m * element_length_m**2 / 2.0
        current_shear_kN += line_load_kN_per_m * element_length_m

    return [
        DiagramSeries(diagram_type=ResultDiagramType.DEFLECTION, unit="mm", points=deflection_points),
        DiagramSeries(diagram_type=ResultDiagramType.ROTATION, unit="rad", points=rotation_points),
        DiagramSeries(diagram_type=ResultDiagramType.SHEAR, unit="kN", points=shear_points),
        DiagramSeries(diagram_type=ResultDiagramType.MOMENT, unit="kNm", points=moment_points),
    ]


def build_analysis_summary(
    mesh: FEMMesh,
    diagrams: list[DiagramSeries],
) -> BeamAnalysisSummary:
    deflection_series = next(series for series in diagrams if series.diagram_type == ResultDiagramType.DEFLECTION)
    shear_series = next(series for series in diagrams if series.diagram_type == ResultDiagramType.SHEAR)
    moment_series = next(series for series in diagrams if series.diagram_type == ResultDiagramType.MOMENT)

    max_deflection_point = min(deflection_series.points, key=lambda point: point.value)
    max_moment_point = max(moment_series.points, key=lambda point: abs(point.value))
    max_shear_point = max(shear_series.points, key=lambda point: abs(point.value))

    return BeamAnalysisSummary(
        total_nodes=len(mesh.nodes),
        total_elements=len(mesh.elements),
        max_deflection_mm=abs(max_deflection_point.value),
        max_deflection_position_m=max_deflection_point.x_m,
        max_moment_kNm=abs(max_moment_point.value),
        max_moment_position_m=max_moment_point.x_m,
        max_shear_kN=abs(max_shear_point.value),
        max_shear_position_m=max_shear_point.x_m,
    )


def analyze_beam(request: BeamAnalysisRequest) -> BeamAnalysisResponse:
    mesh = generate_uniform_beam_mesh(request)
    global_stiffness = assemble_global_stiffness(mesh, request.material, request.section)
    global_load = assemble_global_load_vector(request, mesh)
    displacements = solve_beam_displacements(request, mesh, global_stiffness, global_load)
    reactions = reaction_vector(global_stiffness, displacements, global_load)

    node_results = build_node_results(mesh, displacements)
    element_results = build_element_results(mesh)
    diagram_series = build_diagram_series(request, mesh, request.material, request.section, displacements)
    reaction_results = build_reaction_results(request, mesh, reactions)
    summary = build_analysis_summary(mesh, diagram_series)

    return BeamAnalysisResponse(
        summary=summary,
        nodes=node_results,
        elements=element_results,
        diagrams=diagram_series,
        reactions=reaction_results,
    )
