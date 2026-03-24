from __future__ import annotations

from app.schemas.actions import (
    ActionCategory,
    CombinationType,
    GeneratedCombination,
    GeneratedCombinationSet,
    ProjectAction,
    ProjectActionCatalog,
    CombinationTerm,
)


ULS_PERMANENT_GAMMA = 1.35
ULS_VARIABLE_GAMMA = 1.50
SLS_GAMMA = 1.0


def _validate_catalog(action_catalog: ProjectActionCatalog) -> None:
    for action in action_catalog.actions:
        if action.pattern.category == ActionCategory.VARIABLE and action.combination_factors is None:
            raise ValueError(
                f"Variable action '{action.id}' requires combination_factors with psi values."
            )


def _representative_label_and_factor(
    action: ProjectAction,
    combination_type: CombinationType,
    leading: bool,
) -> tuple[str, float]:
    if action.pattern.category == ActionCategory.PERMANENT:
        return ("Gk", 1.0)

    factors = action.combination_factors
    if factors is None:
        raise ValueError(f"Variable action '{action.id}' requires combination factors.")

    if combination_type == CombinationType.ULS_FUNDAMENTAL:
        return ("Qk", 1.0) if leading else ("psi0", factors.psi0)
    if combination_type == CombinationType.SLS_CHARACTERISTIC:
        return ("Qk", 1.0) if leading else ("psi0", factors.psi0)
    if combination_type == CombinationType.SLS_FREQUENT:
        return ("psi1", factors.psi1) if leading else ("psi2", factors.psi2)
    if combination_type == CombinationType.SLS_QUASI_PERMANENT:
        return ("psi2", factors.psi2)

    raise ValueError(f"Unsupported combination type: {combination_type}")


def _partial_factor(action: ProjectAction, combination_type: CombinationType) -> float:
    if combination_type == CombinationType.ULS_FUNDAMENTAL:
        return ULS_PERMANENT_GAMMA if action.pattern.category == ActionCategory.PERMANENT else ULS_VARIABLE_GAMMA
    return SLS_GAMMA


def _build_combination(
    action_catalog: ProjectActionCatalog,
    combination_type: CombinationType,
    leading_action: ProjectAction | None,
) -> GeneratedCombination:
    terms: list[CombinationTerm] = []

    for action in action_catalog.actions:
        is_leading = leading_action is not None and action.id == leading_action.id
        factor_label, representative_factor = _representative_label_and_factor(
            action,
            combination_type,
            is_leading,
        )
        partial_factor = _partial_factor(action, combination_type)
        design_value = action.pattern.value_kN_per_m2 * representative_factor * partial_factor
        terms.append(
            CombinationTerm(
                action_id=action.id,
                action_name=action.pattern.name,
                action_type=action.pattern.action_type,
                category=action.pattern.category,
                source_standard=action.pattern.source_standard,
                characteristic_value_kN_per_m2=action.pattern.value_kN_per_m2,
                factor_label=factor_label,
                representative_factor=representative_factor,
                partial_factor=partial_factor,
                design_value_kN_per_m2=design_value,
                leading=is_leading,
            )
        )

    expression = {
        CombinationType.ULS_FUNDAMENTAL: "ULS fundamental: Gk + leading Qk + accompanying psi0 Qk",
        CombinationType.SLS_CHARACTERISTIC: "SLS characteristic: Gk + leading Qk + accompanying psi0 Qk",
        CombinationType.SLS_FREQUENT: "SLS frequent: Gk + leading psi1 Qk + accompanying psi2 Qk",
        CombinationType.SLS_QUASI_PERMANENT: "SLS quasi-permanent: Gk + psi2 Qk",
    }[combination_type]

    return GeneratedCombination(
        combination_type=combination_type,
        expression=expression,
        leading_action_id=leading_action.id if leading_action else None,
        terms=terms,
        total_design_value_kN_per_m2=sum(term.design_value_kN_per_m2 for term in terms),
    )


def generate_combinations(action_catalog: ProjectActionCatalog) -> GeneratedCombinationSet:
    _validate_catalog(action_catalog)

    permanent_actions = [
        action for action in action_catalog.actions if action.pattern.category == ActionCategory.PERMANENT
    ]
    variable_actions = [
        action for action in action_catalog.actions if action.pattern.category == ActionCategory.VARIABLE
    ]

    if not permanent_actions and not variable_actions:
        return GeneratedCombinationSet(combinations=[])

    combinations: list[GeneratedCombination] = []

    if variable_actions:
        for leading_action in variable_actions:
            combinations.append(
                _build_combination(action_catalog, CombinationType.ULS_FUNDAMENTAL, leading_action)
            )
            combinations.append(
                _build_combination(action_catalog, CombinationType.SLS_CHARACTERISTIC, leading_action)
            )
            combinations.append(
                _build_combination(action_catalog, CombinationType.SLS_FREQUENT, leading_action)
            )

        combinations.append(
            _build_combination(action_catalog, CombinationType.SLS_QUASI_PERMANENT, None)
        )
    else:
        combinations.append(
            _build_combination(action_catalog, CombinationType.ULS_FUNDAMENTAL, None)
        )
        combinations.append(
            _build_combination(action_catalog, CombinationType.SLS_CHARACTERISTIC, None)
        )
        combinations.append(
            _build_combination(action_catalog, CombinationType.SLS_FREQUENT, None)
        )
        combinations.append(
            _build_combination(action_catalog, CombinationType.SLS_QUASI_PERMANENT, None)
        )

    return GeneratedCombinationSet(combinations=combinations)
