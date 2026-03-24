from __future__ import annotations

from app.domain.combinations import generate_combinations
from app.schemas.actions import ActionType, CombinationType, GeneratedCombination
from app.schemas.floor_joist import (
    ActiveDeflectionCriterion,
    AppliedLoads,
    CombinationCalculationCase,
    CheckResult,
    FloorJoistCalculationRequest,
    FloorJoistCombinationCalculationRequest,
    FloorJoistCombinationCalculationResponse,
    FloorJoistCalculationResponse,
    FloorJoistGeometry,
    IntermediateValues,
    LimitStateSummary,
    NationalAnnexProfile,
    ServiceabilitySummary,
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
    variable_area_load_kN_per_m2: float,
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

    if variable_area_load_kN_per_m2 == 0:
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


def _build_calculation_response(
    geometry: FloorJoistGeometry,
    timber: TimberProperties,
    criteria,
    total_area_load_kN_per_m2: float,
    variable_area_load_kN_per_m2: float,
    check_names: tuple[str, ...] = ("bending", "shear", "deflection"),
):
    line_load_kN_per_m = total_area_load_kN_per_m2 * geometry.spacing_m

    inertia_mm4 = rectangular_section_inertia_mm4(geometry.width_mm, geometry.depth_mm)
    section_modulus_mm3 = rectangular_section_modulus_mm3(geometry.width_mm, geometry.depth_mm)
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

    check_templates = {
        "bending": CheckResult(
            check="bending",
            demand=bending_mpa,
            capacity=timber.allowable_bending_stress_mpa,
            utilization=bending_ratio,
            unit="MPa",
            passed=bending_ratio <= 1.0,
        ),
        "shear": CheckResult(
            check="shear",
            demand=shear_mpa,
            capacity=timber.allowable_shear_stress_mpa,
            utilization=shear_ratio,
            unit="MPa",
            passed=shear_ratio <= 1.0,
        ),
        "deflection": CheckResult(
            check="deflection",
            demand=deflection_mm_value,
            capacity=allowable_deflection_value,
            utilization=deflection_ratio,
            unit="mm",
            passed=deflection_ratio <= 1.0,
        ),
    }
    checks = [check_templates[name] for name in check_names]

    warnings = _warning_messages(geometry, timber, variable_area_load_kN_per_m2, deflection_mm_value)
    passed = all(check.passed for check in checks)

    return {
        "summary": {
            "passed": passed,
            "governing_check": max(checks, key=lambda item: item.utilization).check if checks else "deflection",
        },
        "results": IntermediateValues(
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
        "checks": checks,
        "warnings": warnings,
    }


def _combination_area_loads(combination: GeneratedCombination) -> tuple[float, float]:
    total_area_load_kN_per_m2 = sum(term.design_value_kN_per_m2 for term in combination.terms)
    variable_area_load_kN_per_m2 = sum(
        term.design_value_kN_per_m2 for term in combination.terms if term.action_type != ActionType.PERMANENT
    )
    return total_area_load_kN_per_m2, variable_area_load_kN_per_m2


def _active_deflection_ratio(criteria) -> float:
    return {
        ActiveDeflectionCriterion.FRAGILE_ELEMENTS: 500.0,
        ActiveDeflectionCriterion.ORDINARY_ELEMENTS: 400.0,
        ActiveDeflectionCriterion.WITH_PLASTER_CEILING: 300.0,
        ActiveDeflectionCriterion.WITHOUT_PLASTER_CEILING: 200.0,
    }[criteria.active_deflection_criterion]


def _sls_checks_for_combination(
    combination: GeneratedCombination,
    geometry: FloorJoistGeometry,
    timber: TimberProperties,
    criteria,
    total_area_load_kN_per_m2: float,
    variable_area_load_kN_per_m2: float,
) -> tuple[IntermediateValues, list[CheckResult], list[WarningMessage], bool]:
    calculation = _build_calculation_response(
        geometry,
        timber,
        criteria,
        total_area_load_kN_per_m2,
        variable_area_load_kN_per_m2,
        check_names=(),
    )
    results = calculation["results"]
    warnings = calculation["warnings"]

    checks: list[CheckResult] = []

    if combination.combination_type == CombinationType.SLS_CHARACTERISTIC:
        active_limit = allowable_deflection_mm(geometry.span_m, _active_deflection_ratio(criteria))
        instantaneous_limit = allowable_deflection_mm(geometry.span_m, 350.0)
        checks.append(
            CheckResult(
                check="deflection_active",
                demand=results.deflection_mm,
                capacity=active_limit,
                utilization=utilization_ratio(results.deflection_mm, active_limit),
                unit="mm",
                passed=results.deflection_mm <= active_limit,
            )
        )
        checks.append(
            CheckResult(
                check="deflection_instantaneous",
                demand=results.deflection_mm,
                capacity=instantaneous_limit,
                utilization=utilization_ratio(results.deflection_mm, instantaneous_limit),
                unit="mm",
                passed=results.deflection_mm <= instantaneous_limit,
            )
        )
    elif combination.combination_type == CombinationType.SLS_QUASI_PERMANENT:
        final_limit = allowable_deflection_mm(geometry.span_m, 300.0)
        checks.append(
            CheckResult(
                check="deflection_final",
                demand=results.deflection_mm,
                capacity=final_limit,
                utilization=utilization_ratio(results.deflection_mm, final_limit),
                unit="mm",
                passed=results.deflection_mm <= final_limit,
            )
        )

    passed = all(check.passed for check in checks) if checks else True
    return results, checks, warnings, passed


def _national_annex_notes(criteria) -> list[str]:
    if criteria.national_annex_profile != NationalAnnexProfile.SPAIN_TIMBER_BUILDINGS:
        return []

    return [
        "Spanish timber annex profile enabled for building members under AN/UNE-EN 1995-1-1.",
        "Service class default kept at class 1, which matches intermediate floors between habitable spaces in the Spanish annex.",
        "SLS deflection defaults follow the Spanish annex limits for active, floor comfort, and final deflection.",
        "ULS resistance still uses the user-provided allowable timber stresses; characteristic strengths, kmod, and kdef are not yet modeled in this version.",
        "For EN 1990 buildings, the Spanish national annex values are not fully fixed in the MITMA annex available publicly, so action combination rules remain on the generic Eurocode basis already implemented.",
    ]


def calculate_floor_joist(
    request: FloorJoistCalculationRequest,
) -> FloorJoistCalculationResponse:
    geometry = request.geometry
    timber = request.timber
    loads = request.loads
    criteria = request.criteria

    calculation = _build_calculation_response(
        geometry,
        timber,
        criteria,
        loads.total_area_load_kN_per_m2,
        loads.imposed_load_kN_per_m2,
    )

    return FloorJoistCalculationResponse(
        summary=calculation["summary"],
        inputs=request,
        results=calculation["results"],
        checks=calculation["checks"],
        warnings=calculation["warnings"],
    )


def calculate_floor_joist_with_combinations(
    request: FloorJoistCombinationCalculationRequest,
) -> FloorJoistCombinationCalculationResponse:
    generated_combinations = generate_combinations(request.action_catalog)
    uls_cases: list[CombinationCalculationCase] = []
    sls_cases: list[CombinationCalculationCase] = []

    for combination in generated_combinations.combinations:
        total_area_load_kN_per_m2, variable_area_load_kN_per_m2 = _combination_area_loads(combination)
        if combination.combination_type == CombinationType.ULS_FUNDAMENTAL:
            calculation = _build_calculation_response(
                request.geometry,
                request.timber,
                request.criteria,
                total_area_load_kN_per_m2,
                variable_area_load_kN_per_m2,
                check_names=("bending", "shear"),
            )
            uls_cases.append(
                CombinationCalculationCase(
                    combination=combination,
                    summary=calculation["summary"],
                    results=calculation["results"],
                    checks=calculation["checks"],
                    warnings=calculation["warnings"],
                )
            )
        elif combination.combination_type in {
            CombinationType.SLS_CHARACTERISTIC,
            CombinationType.SLS_QUASI_PERMANENT,
        }:
            results, checks, warnings, passed = _sls_checks_for_combination(
                combination,
                request.geometry,
                request.timber,
                request.criteria,
                total_area_load_kN_per_m2,
                variable_area_load_kN_per_m2,
            )
            if checks:
                sls_cases.append(
                    CombinationCalculationCase(
                        combination=combination,
                        summary={
                            "passed": passed,
                            "governing_check": max(checks, key=lambda item: item.utilization).check,
                        },
                        results=results,
                        checks=checks,
                        warnings=warnings,
                    )
                )

    governing_uls_case = max(
        uls_cases,
        key=lambda case: max(check.utilization for check in case.checks),
    )
    governing_uls_check = max(governing_uls_case.checks, key=lambda check: check.utilization)
    governing_sls_case = max(
        sls_cases,
        key=lambda case: max(check.utilization for check in case.checks),
    )
    governing_sls_check = max(governing_sls_case.checks, key=lambda check: check.utilization)

    return FloorJoistCombinationCalculationResponse(
        summary={
            "passed": all(case.summary.passed for case in uls_cases + sls_cases),
            "uls_passed": all(case.summary.passed for case in uls_cases),
            "sls_passed": all(case.summary.passed for case in sls_cases),
        },
        inputs=request,
        national_annex_notes=_national_annex_notes(request.criteria),
        uls_summary=LimitStateSummary(
            passed=all(case.summary.passed for case in uls_cases),
            governing_check=governing_uls_check.check,
            governing_combination_type=governing_uls_case.combination.combination_type,
            governing_leading_action_id=governing_uls_case.combination.leading_action_id,
        ),
        sls_summary=ServiceabilitySummary(
            passed=all(case.summary.passed for case in sls_cases),
            governing_check=governing_sls_check.check,
            governing_combination_type=governing_sls_case.combination.combination_type,
            governing_leading_action_id=governing_sls_case.combination.leading_action_id,
        ),
        uls_combinations=uls_cases,
        sls_combinations=sls_cases,
    )
