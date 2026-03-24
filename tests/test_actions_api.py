from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_action_combinations_endpoint():
    payload = {
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
    }

    response = client.post("/actions/combinations", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert len(body["combinations"]) == 4
    assert body["combinations"][0]["leading_action_id"] == "q_imposed"
