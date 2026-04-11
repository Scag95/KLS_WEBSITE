from fastapi import APIRouter

from app.domain.combinations import generate_combinations
from app.domain.calculator import calculate_floor_joist, calculate_floor_joist_with_combinations
from app.domain.fem import analyze_beam
from app.schemas.actions import GeneratedCombinationSet, ProjectActionCatalog
from app.schemas.fem import BeamAnalysisRequest, BeamAnalysisResponse
from app.schemas.floor_joist import (
    FloorJoistCalculationRequest,
    FloorJoistCalculationResponse,
    FloorJoistCombinationCalculationRequest,
    FloorJoistCombinationCalculationResponse,
)
from app.domain.kertoripa.calculator import calculate_kerto_ripa
from app.schemas.kertoripa import KertoRipaCalculationRequest, KertoRipaCalculationResponse

router = APIRouter()


@router.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/calculate/floor-joist",
    response_model=FloorJoistCalculationResponse,
    tags=["calculations"],
)
def calculate_floor_joist_endpoint(
    payload: FloorJoistCalculationRequest,
) -> FloorJoistCalculationResponse:
    return calculate_floor_joist(payload)


@router.post(
    "/calculate/floor-joist/combinations",
    response_model=FloorJoistCombinationCalculationResponse,
    tags=["calculations"],
)
def calculate_floor_joist_with_combinations_endpoint(
    payload: FloorJoistCombinationCalculationRequest,
) -> FloorJoistCombinationCalculationResponse:
    return calculate_floor_joist_with_combinations(payload)


@router.post(
    "/calculate/kerto-ripa",
    response_model=KertoRipaCalculationResponse,
    tags=["calculations"],
)
def calculate_kerto_ripa_endpoint(
    payload: KertoRipaCalculationRequest,
) -> KertoRipaCalculationResponse:
    return calculate_kerto_ripa(payload)


@router.post(
    "/analyze/beam",
    response_model=BeamAnalysisResponse,
    tags=["analysis"],
)
def analyze_beam_endpoint(payload: BeamAnalysisRequest) -> BeamAnalysisResponse:
    return analyze_beam(payload)


@router.post(
    "/actions/combinations",
    response_model=GeneratedCombinationSet,
    tags=["actions"],
)
def generate_action_combinations(payload: ProjectActionCatalog) -> GeneratedCombinationSet:
    return generate_combinations(payload)
