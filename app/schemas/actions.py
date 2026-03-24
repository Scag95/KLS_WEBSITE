from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class ActionCategory(StrEnum):
    PERMANENT = "permanent"
    VARIABLE = "variable"


class ActionType(StrEnum):
    PERMANENT = "permanent"
    IMPOSED = "imposed"
    SNOW = "snow"
    WIND = "wind"


class EurocodeActionStandard(StrEnum):
    EN_1991_1_1 = "EN 1991-1-1"
    EN_1991_1_3 = "EN 1991-1-3"
    EN_1991_1_4 = "EN 1991-1-4"


class LoadDistribution(StrEnum):
    UNIFORM = "uniform"
    LINE = "line"
    POINT = "point"
    PATCH = "patch"


class PermanentActionOrigin(StrEnum):
    SELF_WEIGHT = "self_weight"
    NON_STRUCTURAL = "non_structural"
    FIXED_EQUIPMENT = "fixed_equipment"


class ImposedLoadCategory(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"


class SnowLoadPattern(StrEnum):
    UNIFORM = "uniform"
    UNBALANCED = "unbalanced"
    DRIFT = "drift"


class WindLoadPattern(StrEnum):
    PRESSURE = "pressure"
    SUCTION = "suction"


class CombinationFactorSet(BaseModel):
    psi0: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Combination value factor for variable actions.",
    )
    psi1: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Frequent value factor for variable actions.",
    )
    psi2: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Quasi-permanent value factor for variable actions.",
    )


class BaseActionPattern(BaseModel):
    name: str = Field(..., min_length=1, description="Human-readable identifier for the action pattern.")
    distribution: LoadDistribution = Field(
        default=LoadDistribution.UNIFORM,
        description="Spatial representation of the action on the structural element.",
    )
    value_kN_per_m2: float = Field(
        ...,
        ge=0,
        description="Characteristic area action value in kN/m2.",
    )
    description: str | None = Field(
        default=None,
        description="Optional traceability note for UI or reports.",
    )


class PermanentActionPattern(BaseActionPattern):
    action_type: Literal[ActionType.PERMANENT] = ActionType.PERMANENT
    category: Literal[ActionCategory.PERMANENT] = ActionCategory.PERMANENT
    source_standard: Literal[EurocodeActionStandard.EN_1991_1_1] = EurocodeActionStandard.EN_1991_1_1
    origin: PermanentActionOrigin = Field(
        ...,
        description="Permanent action origin according to EN 1991-1-1 concepts.",
    )


class ImposedActionPattern(BaseActionPattern):
    action_type: Literal[ActionType.IMPOSED] = ActionType.IMPOSED
    category: Literal[ActionCategory.VARIABLE] = ActionCategory.VARIABLE
    source_standard: Literal[EurocodeActionStandard.EN_1991_1_1] = EurocodeActionStandard.EN_1991_1_1
    imposed_load_category: ImposedLoadCategory | None = Field(
        default=None,
        description="Optional EN 1991-1-1 occupancy category for imposed loads.",
    )


class SnowActionPatternModel(BaseActionPattern):
    action_type: Literal[ActionType.SNOW] = ActionType.SNOW
    category: Literal[ActionCategory.VARIABLE] = ActionCategory.VARIABLE
    source_standard: Literal[EurocodeActionStandard.EN_1991_1_3] = EurocodeActionStandard.EN_1991_1_3
    snow_pattern: SnowLoadPattern = Field(
        default=SnowLoadPattern.UNIFORM,
        description="Snow load pattern for the structural situation under EN 1991-1-3.",
    )


class WindActionPatternModel(BaseActionPattern):
    action_type: Literal[ActionType.WIND] = ActionType.WIND
    category: Literal[ActionCategory.VARIABLE] = ActionCategory.VARIABLE
    source_standard: Literal[EurocodeActionStandard.EN_1991_1_4] = EurocodeActionStandard.EN_1991_1_4
    wind_pattern: WindLoadPattern = Field(
        ...,
        description="Wind action sign or effect family under EN 1991-1-4.",
    )


ActionPattern = Annotated[
    Union[
        PermanentActionPattern,
        ImposedActionPattern,
        SnowActionPatternModel,
        WindActionPatternModel,
    ],
    Field(discriminator="action_type"),
]


class ActionPatternSet(BaseModel):
    actions: list[ActionPattern] = Field(
        default_factory=list,
        description="Collection of characteristic actions available for combinations or checks.",
    )


class ProjectAction(BaseModel):
    id: str = Field(..., min_length=1, description="Stable identifier for the project action.")
    pattern: ActionPattern
    combination_factors: CombinationFactorSet | None = Field(
        default=None,
        description=(
            "Representative value factors used by EN 1990 combinations. "
            "Required for variable actions and omitted for permanent actions."
        ),
    )


class ProjectActionCatalog(BaseModel):
    actions: list[ProjectAction] = Field(
        default_factory=list,
        description="Project-specific action library used to generate combinations.",
    )


class CombinationType(StrEnum):
    ULS_FUNDAMENTAL = "uls_fundamental"
    SLS_CHARACTERISTIC = "sls_characteristic"
    SLS_FREQUENT = "sls_frequent"
    SLS_QUASI_PERMANENT = "sls_quasi_permanent"


class VariableActionFactorMode(StrEnum):
    CHARACTERISTIC = "characteristic"
    PSI0 = "psi0"
    PSI1 = "psi1"
    PSI2 = "psi2"


class CombinationTerm(BaseModel):
    action_id: str
    action_name: str
    action_type: ActionType
    category: ActionCategory
    source_standard: EurocodeActionStandard
    characteristic_value_kN_per_m2: float
    factor_label: Literal["Gk", "Qk", "psi0", "psi1", "psi2"]
    representative_factor: float = Field(..., ge=0)
    partial_factor: float = Field(..., ge=0)
    design_value_kN_per_m2: float = Field(..., ge=0)
    leading: bool = False


class GeneratedCombination(BaseModel):
    combination_type: CombinationType
    expression: str = Field(
        ...,
        description="Human-readable summary of the representative combination logic.",
    )
    leading_action_id: str | None = Field(
        default=None,
        description="Leading variable action when relevant.",
    )
    terms: list[CombinationTerm]
    total_design_value_kN_per_m2: float = Field(..., ge=0)


class GeneratedCombinationSet(BaseModel):
    combinations: list[GeneratedCombination] = Field(default_factory=list)
