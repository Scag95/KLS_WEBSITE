from app.domain.combinations import generate_combinations
from app.schemas.actions import ProjectActionCatalog


def build_catalog() -> ProjectActionCatalog:
    return ProjectActionCatalog.model_validate(
        {
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
                {
                    "id": "q_wind",
                    "pattern": {
                        "action_type": "wind",
                        "name": "Wind suction",
                        "wind_pattern": "suction",
                        "value_kN_per_m2": 0.6,
                    },
                    "combination_factors": {
                        "psi0": 0.6,
                        "psi1": 0.2,
                        "psi2": 0.0,
                    },
                },
            ]
        }
    )


def test_generate_combinations_creates_one_set_per_leading_variable_plus_quasi_permanent():
    combinations = generate_combinations(build_catalog())

    assert len(combinations.combinations) == 10
    assert sum(1 for item in combinations.combinations if item.combination_type == "uls_fundamental") == 3
    assert sum(1 for item in combinations.combinations if item.combination_type == "sls_characteristic") == 3
    assert sum(1 for item in combinations.combinations if item.combination_type == "sls_frequent") == 3
    assert sum(1 for item in combinations.combinations if item.combination_type == "sls_quasi_permanent") == 1


def test_uls_combination_uses_leading_variable_and_psi0_for_accompanying_actions():
    combinations = generate_combinations(build_catalog())
    uls_imposed_leading = next(
        item
        for item in combinations.combinations
        if item.combination_type == "uls_fundamental" and item.leading_action_id == "q_imposed"
    )

    imposed_term = next(term for term in uls_imposed_leading.terms if term.action_id == "q_imposed")
    snow_term = next(term for term in uls_imposed_leading.terms if term.action_id == "q_snow")
    wind_term = next(term for term in uls_imposed_leading.terms if term.action_id == "q_wind")

    assert imposed_term.factor_label == "Qk"
    assert imposed_term.design_value_kN_per_m2 == 3.0
    assert snow_term.factor_label == "psi0"
    assert round(snow_term.design_value_kN_per_m2, 3) == 0.6
    assert round(wind_term.design_value_kN_per_m2, 3) == 0.54
    assert round(uls_imposed_leading.total_design_value_kN_per_m2, 3) == 6.165


def test_sls_quasi_permanent_uses_psi2_for_all_variable_actions():
    combinations = generate_combinations(build_catalog())
    quasi_permanent = next(
        item for item in combinations.combinations if item.combination_type == "sls_quasi_permanent"
    )

    imposed_term = next(term for term in quasi_permanent.terms if term.action_id == "q_imposed")
    snow_term = next(term for term in quasi_permanent.terms if term.action_id == "q_snow")
    wind_term = next(term for term in quasi_permanent.terms if term.action_id == "q_wind")

    assert imposed_term.factor_label == "psi2"
    assert imposed_term.design_value_kN_per_m2 == 0.6
    assert snow_term.design_value_kN_per_m2 == 0.0
    assert wind_term.design_value_kN_per_m2 == 0.0
    assert quasi_permanent.total_design_value_kN_per_m2 == 2.1


def test_variable_actions_require_combination_factors():
    try:
        generate_combinations(
            ProjectActionCatalog.model_validate(
                {
                    "actions": [
                        {
                            "id": "q_imposed",
                            "pattern": {
                                "action_type": "imposed",
                                "name": "Residential imposed load",
                                "value_kN_per_m2": 2.0,
                            },
                        }
                    ]
                }
            )
        )
    except ValueError as error:
        assert "combination_factors" in str(error)
    else:
        raise AssertionError("Variable actions must require psi factors for combinations.")
