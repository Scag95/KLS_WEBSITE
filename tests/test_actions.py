from pydantic import TypeAdapter, ValidationError

from app.schemas.actions import (
    ActionCategory,
    ActionPattern,
    ActionType,
    EurocodeActionStandard,
    ImposedLoadCategory,
    PermanentActionOrigin,
    SnowLoadPattern,
)


action_pattern_adapter = TypeAdapter(ActionPattern)


def test_permanent_action_pattern_maps_to_en_1991_1_1():
    action = action_pattern_adapter.validate_python(
        {
            "action_type": "permanent",
            "name": "Self weight of timber joists",
            "origin": "self_weight",
            "value_kN_per_m2": 0.7,
        }
    )

    assert action.action_type == ActionType.PERMANENT
    assert action.category == ActionCategory.PERMANENT
    assert action.source_standard == EurocodeActionStandard.EN_1991_1_1
    assert action.origin == PermanentActionOrigin.SELF_WEIGHT


def test_imposed_action_pattern_maps_to_variable_category():
    action = action_pattern_adapter.validate_python(
        {
            "action_type": "imposed",
            "name": "Residential imposed load",
            "imposed_load_category": "A",
            "value_kN_per_m2": 2.0,
        }
    )

    assert action.action_type == ActionType.IMPOSED
    assert action.category == ActionCategory.VARIABLE
    assert action.source_standard == EurocodeActionStandard.EN_1991_1_1
    assert action.imposed_load_category == ImposedLoadCategory.A


def test_snow_action_pattern_defaults_to_uniform_pattern():
    action = action_pattern_adapter.validate_python(
        {
            "action_type": "snow",
            "name": "Snow on pitched roof",
            "value_kN_per_m2": 0.8,
        }
    )

    assert action.category == ActionCategory.VARIABLE
    assert action.source_standard == EurocodeActionStandard.EN_1991_1_3
    assert action.snow_pattern == SnowLoadPattern.UNIFORM


def test_invalid_negative_action_value_is_rejected():
    try:
        action_pattern_adapter.validate_python(
            {
                "action_type": "wind",
                "name": "Wind suction",
                "wind_pattern": "suction",
                "value_kN_per_m2": -0.5,
            }
        )
    except ValidationError as error:
        assert "value_kN_per_m2" in str(error)
    else:
        raise AssertionError("Negative characteristic actions must be rejected.")
