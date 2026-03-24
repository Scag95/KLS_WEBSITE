from fastapi import APIRouter

from app.domain.combinations import generate_combinations
from app.domain.calculator import calculate_floor_joist
from app.schemas.actions import GeneratedCombinationSet, ProjectActionCatalog
from app.schemas.floor_joist import FloorJoistCalculationRequest, FloorJoistCalculationResponse

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
    "/actions/combinations",
    response_model=GeneratedCombinationSet,
    tags=["actions"],
)
def generate_action_combinations(payload: ProjectActionCatalog) -> GeneratedCombinationSet:
    return generate_combinations(payload)
