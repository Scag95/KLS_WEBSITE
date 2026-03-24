from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_floor_joist_endpoint_returns_traceable_result():
    payload = {
        "project_name": "API case",
        "geometry": {
            "span_m": 4.0,
            "spacing_m": 0.4,
            "width_mm": 63.0,
            "depth_mm": 200.0,
        },
        "timber": {
            "grade": "C24",
            "modulus_of_elasticity_mpa": 11000.0,
            "allowable_bending_stress_mpa": 11.0,
            "allowable_shear_stress_mpa": 1.2,
        },
        "loads": {
            "dead_load_kN_per_m2": 1.5,
            "imposed_load_kN_per_m2": 2.0,
            "additional_dead_load_kN_per_m2": 0.5,
        },
        "criteria": {
            "design_standard": "concept-v1",
            "max_deflection_ratio": 300.0,
        },
    }

    response = client.post("/calculate/floor-joist", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["summary"]["passed"] is True
    assert body["summary"]["governing_check"] == "deflection"
    assert body["inputs"]["criteria"]["design_standard"] == "concept-v1"
    assert body["results"]["line_load_kN_per_m"] == 1.6
    assert len(body["checks"]) == 3


def test_floor_joist_endpoint_rejects_invalid_input():
    payload = {
        "geometry": {
            "span_m": -1.0,
            "spacing_m": 0.4,
            "width_mm": 63.0,
            "depth_mm": 200.0,
        },
        "timber": {
            "grade": "C24",
            "modulus_of_elasticity_mpa": 11000.0,
            "allowable_bending_stress_mpa": 11.0,
            "allowable_shear_stress_mpa": 1.2,
        },
        "loads": {
            "dead_load_kN_per_m2": 1.5,
            "imposed_load_kN_per_m2": 2.0,
        },
    }

    response = client.post("/calculate/floor-joist", json=payload)

    assert response.status_code == 422
