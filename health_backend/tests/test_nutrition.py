import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE_DATE = str(date.today() - timedelta(days=3))

SAMPLE_MEAL = {
    "log_date": BASE_DATE,
    "meal_type": "breakfast",
    "items": [
        {
            "food_name": "Oats",
            "serving_qty": 80.0,
            "serving_unit": "g",
            "calories": 300,
            "protein_g": 10.0,
            "carbs_g": 55.0,
            "fat_g": 6.0,
            "fiber_g": 8.0,
        },
        {
            "food_name": "Banana",
            "serving_qty": 1.0,
            "serving_unit": "medium",
            "calories": 89,
            "protein_g": 1.1,
            "carbs_g": 23.0,
            "fat_g": 0.3,
            "fiber_g": 2.6,
        },
    ],
}


async def test_create_nutrition_log(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/nutrition", headers=auth_headers, json=SAMPLE_MEAL)
    assert resp.status_code == 201
    data = resp.json()
    assert data["meal_type"] == "breakfast"
    assert data["total_calories"] == 389        # 300 + 89
    assert data["total_protein_g"] == 11.1      # 10.0 + 1.1
    assert len(data["items"]) == 2


async def test_macro_aggregation(client: AsyncClient, auth_headers: dict):
    """Verify server-side macro aggregation is correct."""
    d = str(date.today() - timedelta(days=11))
    resp = await client.post("/api/v1/nutrition", headers=auth_headers, json={
        "log_date": d,
        "meal_type": "lunch",
        "items": [
            {"food_name": "Chicken", "serving_qty": 150, "serving_unit": "g",
             "calories": 248, "protein_g": 46.0, "carbs_g": 0.0, "fat_g": 5.4, "fiber_g": 0.0},
            {"food_name": "Brown Rice", "serving_qty": 200, "serving_unit": "g",
             "calories": 216, "protein_g": 4.5, "carbs_g": 44.8, "fat_g": 1.8, "fiber_g": 3.5},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_calories"] == 464
    assert round(data["total_protein_g"], 1) == 50.5
    assert round(data["total_carbs_g"], 1) == 44.8
    assert round(data["total_fiber_g"], 1) == 3.5


async def test_multiple_meals_same_day(client: AsyncClient, auth_headers: dict):
    """Different meal types on the same day are all allowed."""
    d = str(date.today() - timedelta(days=12))
    for meal in ["breakfast", "lunch", "dinner", "snack"]:
        r = await client.post("/api/v1/nutrition", headers=auth_headers, json={
            "log_date": d,
            "meal_type": meal,
            "items": [{"food_name": "Food", "serving_qty": 100,
                        "serving_unit": "g", "calories": 200}],
        })
        assert r.status_code == 201


async def test_list_nutrition_logs(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/nutrition", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_with_date_filter(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/nutrition",
        headers=auth_headers,
        params={"start_date": BASE_DATE, "end_date": BASE_DATE},
    )
    assert resp.status_code == 200
    logs = resp.json()
    assert all(log["log_date"] == BASE_DATE for log in logs)


async def test_get_nutrition_log_by_id(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=13))
    create_resp = await client.post("/api/v1/nutrition", headers=auth_headers, json={
        "log_date": d,
        "meal_type": "dinner",
        "items": [{"food_name": "Pasta", "serving_qty": 200, "serving_unit": "g", "calories": 320}],
    })
    log_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/nutrition/{log_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == log_id
    assert len(resp.json()["items"]) == 1


async def test_invalid_meal_type(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/nutrition", headers=auth_headers, json={
        "log_date": BASE_DATE,
        "meal_type": "midnight_snack",  # not a valid enum
        "items": [],
    })
    assert resp.status_code == 422


async def test_negative_serving_qty_fails(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=14))
    resp = await client.post("/api/v1/nutrition", headers=auth_headers, json={
        "log_date": d,
        "meal_type": "snack",
        "items": [{"food_name": "Apple", "serving_qty": -1, "serving_unit": "piece"}],
    })
    assert resp.status_code == 422


async def test_delete_nutrition_log(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=15))
    create_resp = await client.post("/api/v1/nutrition", headers=auth_headers, json={
        "log_date": d,
        "meal_type": "snack",
        "items": [{"food_name": "Almonds", "serving_qty": 30, "serving_unit": "g", "calories": 174}],
    })
    log_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/nutrition/{log_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    get_resp = await client.get(f"/api/v1/nutrition/{log_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_nutrition_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/nutrition")
    assert resp.status_code == 403
