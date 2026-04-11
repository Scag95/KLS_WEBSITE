from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.actions import ProjectActionCatalog
from app.schemas.fem import BeamSupport
from app.schemas.floor_joist import ServiceClass, WarningMessage


class KertoRipaSectionType(StrEnum):
    RIBBED_TOP = "ribbed_top"
    RIBBED_BOTTOM = "ribbed_bottom"
    BOX = "box"
    OPEN_BOX = "open_box"


class RibPosition(StrEnum):
    EDGE = "edge"
    MIDDLE = "middle"


class LoadDurationClass(StrEnum):
    PERMANENT = "permanent"
    LONG_TERM = "long_term"
    MEDIUM_TERM = "medium_term"
    SHORT_TERM = "short_term"
    INSTANTANEOUS = "instantaneous"


class KertoRipaCrossSectionInput(BaseModel):
    section_type: KertoRipaSectionType
    element_width_mm: float = Field(..., gt=0, description="Total width of the Kerto-Ripa element in mm.")
    n_ribs: int = Field(..., ge=2, description="Number of ribs (webs), must be >= 2.")
    h_w_mm: float = Field(..., gt=0, description="Height of the rib (web) in mm.")
    b_w_mm: float = Field(..., gt=0, description="Width of the rib (web) in mm.")
    h_f1_mm: float | None = Field(default=None, gt=0, description="Thickness of top slab (Kerto-Q) in mm. Must be sanded thickness.")
    h_f2_mm: float | None = Field(default=None, gt=0, description="Thickness of bottom slab (Kerto-Q) in mm. Must be sanded thickness.")
    b_actual_mm: float | None = Field(default=None, gt=0, description="Actual width of bottom slab per rib (open box only) in mm.")


class KertoRipaSpanInput(BaseModel):
    L_ef_mm: float = Field(..., gt=0, description="Effective calculation span in mm.")
    L_support_mm: float = Field(..., gt=0, description="Support contact length in mm.")
    support_position: str = Field(default="end", description="'end' or 'intermediate'")


class KertoRipaDesignBasis(BaseModel):
    service_class: ServiceClass
    load_duration_class: LoadDurationClass


class KertoRipaCalculationRequest(BaseModel):
    project_name: str | None = None
    cross_section: KertoRipaCrossSectionInput
    span: KertoRipaSpanInput
    supports: list[BeamSupport] = Field(
        ...,
        min_length=2,
        description="Supports applied along the span for FEM analysis.",
    )
    design_basis: KertoRipaDesignBasis
    action_catalog: ProjectActionCatalog


class KertoRipaGeometryResults(BaseModel):
    b_f_mm: float
    b_ef_SLS_top_mm: float
    b_ef_ULS_top_mm: float
    b_ef_SLS_bot_mm: float
    b_ef_ULS_bot_mm: float
    EI_ef_SLS_Nmm2: float
    EI_ef_ULS_Nmm2: float
    neutral_axis_a2_mm: float


class KertoRipaCheckResult(BaseModel):
    check: str
    demand: float
    capacity: float
    utilization: float
    unit: str
    passed: bool
    failure_mode: str | None = None


class KertoRipaCalculationResponse(BaseModel):
    summary: dict[str, Any]
    geometry: KertoRipaGeometryResults
    uls_checks: list[KertoRipaCheckResult]
    sls_checks: list[KertoRipaCheckResult]
    intermediate_values: dict[str, Any]
    warnings: list[WarningMessage]
