from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

from app.schemas.actions import GeneratedCombination, ProjectActionCatalog
from app.schemas.fem import BeamSupport


class FloorJoistGeometry(BaseModel):
    span_m: float = Field(..., gt=0, description="Clear span of the joist in meters.")
    spacing_m: float = Field(..., gt=0, description="Centre-to-centre joist spacing in meters.")
    width_mm: float = Field(..., gt=0, description="Timber joist width in millimeters.")
    depth_mm: float = Field(..., gt=0, description="Timber joist depth in millimeters.")


class TimberProperties(BaseModel):
    grade: str = Field(..., min_length=1, description="Identifier for the timber grade.")
    modulus_of_elasticity_mpa: float = Field(..., gt=0, description="Mean elastic modulus in MPa.")
    allowable_bending_stress_mpa: float = Field(..., gt=0, description="Allowable bending stress in MPa.")
    allowable_shear_stress_mpa: float = Field(..., gt=0, description="Allowable shear stress in MPa.")
    density_kg_per_m3: float | None = Field(
        default=None,
        gt=0,
        description="Optional density for future self-weight or reporting features.",
    )


class NationalAnnexProfile(StrEnum):
    GENERIC = "generic"
    SPAIN_TIMBER_BUILDINGS = "spain_timber_buildings"


class ServiceClass(StrEnum):
    SC1 = "service_class_1"
    SC2 = "service_class_2"
    SC3 = "service_class_3"


class ActiveDeflectionCriterion(StrEnum):
    FRAGILE_ELEMENTS = "fragile_elements"
    ORDINARY_ELEMENTS = "ordinary_elements"
    WITH_PLASTER_CEILING = "with_plaster_ceiling"
    WITHOUT_PLASTER_CEILING = "without_plaster_ceiling"


class AppliedLoads(BaseModel):
    dead_load_kN_per_m2: float = Field(..., ge=0, description="Permanent distributed load in kN/m2.")
    imposed_load_kN_per_m2: float = Field(..., ge=0, description="Variable distributed load in kN/m2.")
    additional_dead_load_kN_per_m2: float = Field(
        default=0.0,
        ge=0,
        description="Additional permanent load reserved for finishes or services.",
    )

    @computed_field
    @property
    def total_area_load_kN_per_m2(self) -> float:
        return (
            self.dead_load_kN_per_m2
            + self.imposed_load_kN_per_m2
            + self.additional_dead_load_kN_per_m2
        )


class DesignCriteria(BaseModel):
    design_standard: str = Field(
        default="concept-v1",
        min_length=1,
        description="Human-readable design basis identifier used for traceability.",
    )
    max_deflection_ratio: float = Field(
        default=300.0,
        gt=0,
        description="Span/ratio serviceability limit for deflection checks.",
    )
    active_deflection_ratio: float = Field(
        default=300.0,
        gt=0,
        description="Span/ratio limit for active deflection under SLS characteristic combinations.",
    )
    instantaneous_deflection_ratio: float = Field(
        default=300.0,
        gt=0,
        description="Span/ratio limit for instantaneous deflection under SLS characteristic combinations.",
    )
    final_deflection_ratio: float = Field(
        default=300.0,
        gt=0,
        description="Span/ratio limit for final deflection under SLS quasi-permanent combinations.",
    )
    national_annex_profile: NationalAnnexProfile = Field(
        default=NationalAnnexProfile.GENERIC,
        description="Calculation profile used to interpret serviceability checks and defaults.",
    )
    service_class: ServiceClass = Field(
        default=ServiceClass.SC1,
        description="Timber service class used by the selected national annex profile.",
    )
    active_deflection_criterion: ActiveDeflectionCriterion = Field(
        default=ActiveDeflectionCriterion.ORDINARY_ELEMENTS,
        description="Spanish timber annex deflection criterion for active deformation checks.",
    )

    @model_validator(mode="after")
    def validate_ratio(self) -> "DesignCriteria":
        if self.max_deflection_ratio < 150:
            raise ValueError("max_deflection_ratio must be at least 150.")
        if self.active_deflection_ratio < 150:
            raise ValueError("active_deflection_ratio must be at least 150.")
        if self.instantaneous_deflection_ratio < 150:
            raise ValueError("instantaneous_deflection_ratio must be at least 150.")
        if self.final_deflection_ratio < 150:
            raise ValueError("final_deflection_ratio must be at least 150.")
        return self


class FloorJoistCalculationRequest(BaseModel):
    project_name: str | None = Field(
        default=None,
        description="Optional project or case label for traceability.",
    )
    geometry: FloorJoistGeometry
    timber: TimberProperties
    supports: list[BeamSupport] = Field(
        ...,
        min_length=2,
        description="Supports used by the joist model and reused by the beam diagram analysis.",
    )
    loads: AppliedLoads
    criteria: DesignCriteria = Field(default_factory=DesignCriteria)

    @model_validator(mode="after")
    def validate_supports(self) -> "FloorJoistCalculationRequest":
        span_length = self.geometry.span_m
        for support in self.supports:
            if support.position_m > span_length:
                raise ValueError("Support position cannot be beyond the joist span.")
        return self


class IntermediateValues(BaseModel):
    line_load_kN_per_m: float
    max_moment_kNm: float
    max_shear_kN: float
    section_inertia_mm4: float
    section_modulus_mm3: float
    bending_stress_mpa: float
    shear_stress_mpa: float
    deflection_mm: float
    allowable_deflection_mm: float


class CheckResult(BaseModel):
    check: Literal[
        "bending",
        "shear",
        "deflection",
        "deflection_active",
        "deflection_instantaneous",
        "deflection_final",
    ]
    demand: float
    capacity: float
    utilization: float
    unit: Literal["MPa", "mm"]
    passed: bool


class WarningMessage(BaseModel):
    code: str
    message: str


class CalculationSummary(BaseModel):
    passed: bool
    governing_check: Literal["bending", "shear", "deflection"]


class CombinationCaseSummary(BaseModel):
    passed: bool
    governing_check: Literal[
        "bending",
        "shear",
        "deflection",
        "deflection_active",
        "deflection_instantaneous",
        "deflection_final",
    ]


class FloorJoistCalculationResponse(BaseModel):
    summary: CalculationSummary
    inputs: FloorJoistCalculationRequest
    results: IntermediateValues
    checks: list[CheckResult]
    warnings: list[WarningMessage]


class FloorJoistCombinationCalculationRequest(BaseModel):
    project_name: str | None = Field(
        default=None,
        description="Optional project or case label for traceability.",
    )
    geometry: FloorJoistGeometry
    timber: TimberProperties
    supports: list[BeamSupport] = Field(
        ...,
        min_length=2,
        description="Supports used by the joist model and reused by the beam diagram analysis.",
    )
    criteria: DesignCriteria = Field(default_factory=DesignCriteria)
    action_catalog: ProjectActionCatalog

    @model_validator(mode="after")
    def validate_supports(self) -> "FloorJoistCombinationCalculationRequest":
        span_length = self.geometry.span_m
        for support in self.supports:
            if support.position_m > span_length:
                raise ValueError("Support position cannot be beyond the joist span.")
        return self


class CombinationCalculationCase(BaseModel):
    combination: GeneratedCombination
    summary: CombinationCaseSummary
    results: IntermediateValues
    checks: list[CheckResult]
    warnings: list[WarningMessage]


class LimitStateSummary(BaseModel):
    passed: bool
    governing_check: Literal["bending", "shear", "deflection"]
    governing_combination_type: str
    governing_leading_action_id: str | None = None


class ServiceabilitySummary(BaseModel):
    passed: bool
    governing_check: Literal["deflection_active", "deflection_instantaneous", "deflection_final"]
    governing_combination_type: str
    governing_leading_action_id: str | None = None


class FloorJoistCombinationCalculationResponse(BaseModel):
    summary: dict[str, bool]
    inputs: FloorJoistCombinationCalculationRequest
    national_annex_notes: list[str]
    uls_summary: LimitStateSummary
    sls_summary: ServiceabilitySummary
    uls_combinations: list[CombinationCalculationCase]
    sls_combinations: list[CombinationCalculationCase]
