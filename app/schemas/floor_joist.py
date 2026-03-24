from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator


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

    @model_validator(mode="after")
    def validate_ratio(self) -> "DesignCriteria":
        if self.max_deflection_ratio < 150:
            raise ValueError("max_deflection_ratio must be at least 150.")
        return self


class FloorJoistCalculationRequest(BaseModel):
    project_name: str | None = Field(
        default=None,
        description="Optional project or case label for traceability.",
    )
    geometry: FloorJoistGeometry
    timber: TimberProperties
    loads: AppliedLoads
    criteria: DesignCriteria = Field(default_factory=DesignCriteria)


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
    check: Literal["bending", "shear", "deflection"]
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


class FloorJoistCalculationResponse(BaseModel):
    summary: CalculationSummary
    inputs: FloorJoistCalculationRequest
    results: IntermediateValues
    checks: list[CheckResult]
    warnings: list[WarningMessage]
