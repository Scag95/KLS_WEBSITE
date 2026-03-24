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


def test_floor_joist_combination_endpoint_returns_combined_results():
    payload = {
        "project_name": "API combined case",
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
        "criteria": {
            "design_standard": "concept-v1",
            "max_deflection_ratio": 300.0,
            "national_annex_profile": "spain_timber_buildings",
            "service_class": "service_class_1",
            "active_deflection_criterion": "ordinary_elements",
        },
        "action_catalog": {
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
            ]
        },
    }

    response = client.post("/calculate/floor-joist/combinations", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert len(body["uls_combinations"]) == 1
    assert len(body["sls_combinations"]) == 2
    assert body["uls_summary"]["governing_combination_type"] == "uls_fundamental"
    assert body["sls_summary"]["governing_check"] in {
        "deflection_active",
        "deflection_instantaneous",
        "deflection_final",
    }


def test_beam_analysis_endpoint_returns_diagrams():
    payload = {
        "project_name": "Beam example",
        "span": {
            "length_m": 4.0,
            "element_count": 4,
        },
        "material": {
            "modulus_of_elasticity_mpa": 11000.0,
        },
        "section": {
            "width_mm": 63.0,
            "depth_mm": 200.0,
        },
        "supports": [
            {"position_m": 0.0, "support_type": "pinned"},
            {"position_m": 4.0, "support_type": "roller"},
        ],
        "loads": [
            {
                "load_type": "distributed",
                "start_m": 0.0,
                "end_m": 4.0,
                "value_kN_per_m": -1.6,
            }
        ],
    }

    response = client.post("/analyze/beam", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["summary"]["max_moment_kNm"] == 3.199999999999992
    assert len(body["diagrams"]) == 4
