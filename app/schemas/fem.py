from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BeamTheory(StrEnum):
    EULER_BERNOULLI = "euler_bernoulli"


class SupportType(StrEnum):
    FIXED = "fixed"
    PINNED = "pinned"
    ROLLER = "roller"
    FREE = "free"


class DistributedLoadDirection(StrEnum):
    GLOBAL_Y = "global_y"


class PointLoadDirection(StrEnum):
    GLOBAL_Y = "global_y"


class ResultDiagramType(StrEnum):
    SHEAR = "shear"
    MOMENT = "moment"
    DEFLECTION = "deflection"
    ROTATION = "rotation"


class BeamSpanDefinition(BaseModel):
    length_m: float = Field(..., gt=0, description="Global span length of the beam in meters.")
    #Todo: the user can't specify the number of elements, but we can set a default value and allow them to override it if they want more or fewer elements.
    #Todo: the user can specify the number of span
    element_count: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of finite elements created automatically along the span.",
    )


class BeamMaterial(BaseModel):
    modulus_of_elasticity_mpa: float = Field(
        ...,
        gt=0,
        description="Young's modulus used by the beam finite element model in MPa.",
    )


class BeamSection(BaseModel):
    width_mm: float = Field(..., gt=0)
    depth_mm: float = Field(..., gt=0)

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.depth_mm

    @property
    def inertia_mm4(self) -> float:
        return self.width_mm * self.depth_mm**3 / 12.0


class BeamSupport(BaseModel):
    position_m: float = Field(..., ge=0)
    support_type: SupportType


class DistributedLoad(BaseModel):
    load_type: Literal["distributed"] = "distributed"
    start_m: float = Field(..., ge=0)
    end_m: float = Field(..., ge=0)
    value_kN_per_m: float = Field(
        ...,
        description="Signed line load in kN/m. Negative values act downward by convention.",
    )
    direction: DistributedLoadDirection = DistributedLoadDirection.GLOBAL_Y

    @model_validator(mode="after")
    def validate_range(self) -> "DistributedLoad":
        if self.end_m <= self.start_m:
            raise ValueError("Distributed load end_m must be greater than start_m.")
        return self


class PointLoad(BaseModel):
    load_type: Literal["point"] = "point"
    position_m: float = Field(..., ge=0)
    value_kN: float = Field(
        ...,
        description="Signed point load in kN. Negative values act downward by convention.",
    )
    direction: PointLoadDirection = PointLoadDirection.GLOBAL_Y


class PointMoment(BaseModel):
    load_type: Literal["moment"] = "moment"
    position_m: float = Field(..., ge=0)
    value_kNm: float = Field(
        ...,
        description="Signed nodal moment in kNm. Positive sign follows the local solver convention.",
    )


BeamLoad = DistributedLoad | PointLoad | PointMoment


class BeamAnalysisRequest(BaseModel):
    project_name: str | None = None
    beam_theory: BeamTheory = BeamTheory.EULER_BERNOULLI
    span: BeamSpanDefinition
    material: BeamMaterial
    section: BeamSection
    supports: list[BeamSupport] = Field(
        ...,
        min_length=1,
        description="Supports applied along the global beam axis.",
    )
    loads: list[BeamLoad] = Field(
        default_factory=list,
        description="External actions converted directly into beam loads.",
    )

    @model_validator(mode="after")
    def validate_positions(self) -> "BeamAnalysisRequest":
        span_length = self.span.length_m

        for support in self.supports:
            if support.position_m > span_length:
                raise ValueError("Support position cannot be beyond the beam span.")

        for load in self.loads:
            if isinstance(load, DistributedLoad) and load.end_m > span_length:
                raise ValueError("Distributed load end_m cannot be beyond the beam span.")
            if isinstance(load, (PointLoad, PointMoment)) and load.position_m > span_length:
                raise ValueError("Point load or moment position cannot be beyond the beam span.")

        pinned_or_fixed = [support for support in self.supports if support.support_type != SupportType.FREE]
        if len(pinned_or_fixed) < 2:
            raise ValueError("At least two supports or restraints are required for a stable beam model.")

        return self


class NodeResult(BaseModel):
    node_id: int
    x_m: float
    vertical_displacement_mm: float
    rotation_rad: float


class ElementResult(BaseModel):
    element_id: int
    start_x_m: float
    end_x_m: float
    length_m: float


class DiagramPoint(BaseModel):
    x_m: float
    value: float


class DiagramSeries(BaseModel):
    diagram_type: ResultDiagramType
    unit: str
    points: list[DiagramPoint]


class SupportReaction(BaseModel):
    position_m: float
    vertical_reaction_kN: float
    moment_reaction_kNm: float | None = None


class BeamAnalysisSummary(BaseModel):
    total_nodes: int
    total_elements: int
    max_deflection_mm: float
    max_deflection_position_m: float
    max_moment_kNm: float
    max_moment_position_m: float
    max_shear_kN: float
    max_shear_position_m: float


class BeamAnalysisResponse(BaseModel):
    summary: BeamAnalysisSummary
    nodes: list[NodeResult]
    elements: list[ElementResult]
    diagrams: list[DiagramSeries]
    reactions: list[SupportReaction]
