from __future__ import annotations

from app.schemas.floor_joist import (
    AppliedLoads,
    CheckResult,
    FloorJoistCalculationRequest,
    FloorJoistCalculationResponse,
    FloorJoistGeometry,
    IntermediateValues,
    TimberProperties,
    WarningMessage,
)


MM_PER_M = 1000.0
N_PER_KN = 1000.0


def rectangular_section_inertia_mm4(width_mm: float, depth_mm: float) -> float:
    return width_mm * depth_mm**3 / 12.0


def rectangular_section_modulus_mm3(width_mm: float, depth_mm: float) -> float:
    return width_mm * depth_mm**2 / 6.0


def joist_line_load_kN_per_m(loads: AppliedLoads, geometry: FloorJoistGeometry) -> float:
    return loads.total_area_load_kN_per_m2 * geometry.spacing_m


def max_bending_moment_kNm(uniform_line_load_kN_per_m: float, span_m: float) -> float:
    return uniform_line_load_kN_per_m * span_m**2 / 8.0


def max_shear_force_kN(uniform_line_load_kN_per_m: float, span_m: float) -> float:
    return uniform_line_load_kN_per_m * span_m / 2.0


def bending_stress_mpa(moment_kNm: float, section_modulus_mm3: float) -> float:
    return moment_kNm * 1_000_000.0 / section_modulus_mm3


def shear_stress_mpa(shear_force_kN: float, width_mm: float, depth_mm: float) -> float:
    area_mm2 = width_mm * depth_mm
    return 1.5 * shear_force_kN * N_PER_KN / area_mm2


def instantaneous_deflection_mm(
    uniform_line_load_kN_per_m: float,
    span_m: float,
    modulus_of_elasticity_mpa: float,
    inertia_mm4: float,
) -> float:
    w_n_per_mm = uniform_line_load_kN_per_m
    span_mm = span_m * MM_PER_M
    return (5.0 * w_n_per_mm * span_mm**4) / (384.0 * modulus_of_elasticity_mpa * inertia_mm4)


def allowable_deflection_mm(span_m: float, ratio: float) -> float:
    return span_m * MM_PER_M / ratio


def utilization_ratio(demand: float, capacity: float) -> float:
    if capacity == 0:
        return float("inf")
    return demand / capacity


def _warning_messages(
    geometry: FloorJoistGeometry,
    timber: TimberProperties,
    loads: AppliedLoads,
    deflection_mm_value: float,
) -> list[WarningMessage]:
    warnings: list[WarningMessage] = []

    slenderness_ratio = geometry.span_m * MM_PER_M / geometry.depth_mm
    if slenderness_ratio > 25:
        warnings.append(
            WarningMessage(
                code="SPAN_DEPTH_RATIO_HIGH",
                message=(
                    "The span-to-depth ratio is high for a floor joist and may lead "
                    "to serviceability issues."
                ),
            )
        )

    if loads.imposed_load_kN_per_m2 == 0:
        warnings.append(
            WarningMessage(
                code="ZERO_IMPOSED_LOAD",
                message="Variable load is zero; confirm this matches the intended use case.",
            )
        )

    if timber.modulus_of_elasticity_mpa < 8000:
        warnings.append(
            WarningMessage(
                code="LOW_STIFFNESS_TIMBER",
                message="The selected timber stiffness is low and may control deflection.",
            )
        )

    if deflection_mm_value > 20:
        warnings.append(
            WarningMessage(
                code="HIGH_DEFLECTION_ABSOLUTE",
                message="Calculated deflection is above 20 mm; review comfort and finishes criteria.",
            )
        )

    return warnings


def calculate_floor_joist(
    request: FloorJoistCalculationRequest,
) -> FloorJoistCalculationResponse:
    geometry = request.geometry
    timber = request.timber
    loads = request.loads
    criteria = request.criteria

    inertia_mm4 = rectangular_section_inertia_mm4(geometry.width_mm, geometry.depth_mm)
    section_modulus_mm3 = rectangular_section_modulus_mm3(geometry.width_mm, geometry.depth_mm)
    line_load_kN_per_m = joist_line_load_kN_per_m(loads, geometry)
    moment_kNm = max_bending_moment_kNm(line_load_kN_per_m, geometry.span_m)
    shear_kN = max_shear_force_kN(line_load_kN_per_m, geometry.span_m)
    bending_mpa = bending_stress_mpa(moment_kNm, section_modulus_mm3)
    shear_mpa = shear_stress_mpa(shear_kN, geometry.width_mm, geometry.depth_mm)
    deflection_mm_value = instantaneous_deflection_mm(
        line_load_kN_per_m,
        geometry.span_m,
        timber.modulus_of_elasticity_mpa,
        inertia_mm4,
    )
    allowable_deflection_value = allowable_deflection_mm(
        geometry.span_m,
        criteria.max_deflection_ratio,
    )

    bending_ratio = utilization_ratio(bending_mpa, timber.allowable_bending_stress_mpa)
    shear_ratio = utilization_ratio(shear_mpa, timber.allowable_shear_stress_mpa)
    deflection_ratio = utilization_ratio(deflection_mm_value, allowable_deflection_value)

    checks = [
        CheckResult(
            check="bending",
            demand=bending_mpa,
            capacity=timber.allowable_bending_stress_mpa,
            utilization=bending_ratio,
            unit="MPa",
            passed=bending_ratio <= 1.0,
        ),
        CheckResult(
            check="shear",
            demand=shear_mpa,
            capacity=timber.allowable_shear_stress_mpa,
            utilization=shear_ratio,
            unit="MPa",
            passed=shear_ratio <= 1.0,
        ),
        CheckResult(
            check="deflection",
            demand=deflection_mm_value,
            capacity=allowable_deflection_value,
            utilization=deflection_ratio,
            unit="mm",
            passed=deflection_ratio <= 1.0,
        ),
    ]

    warnings = _warning_messages(geometry, timber, loads, deflection_mm_value)
    passed = all(check.passed for check in checks)

    return FloorJoistCalculationResponse(
        summary={
            "passed": passed,
            "governing_check": max(checks, key=lambda item: item.utilization).check,
        },
        inputs=request,
        results=IntermediateValues(
            line_load_kN_per_m=line_load_kN_per_m,
            max_moment_kNm=moment_kNm,
            max_shear_kN=shear_kN,
            section_inertia_mm4=inertia_mm4,
            section_modulus_mm3=section_modulus_mm3,
            bending_stress_mpa=bending_mpa,
            shear_stress_mpa=shear_mpa,
            deflection_mm=deflection_mm_value,
            allowable_deflection_mm=allowable_deflection_value,
        ),
        checks=checks,
        warnings=warnings,
    )
