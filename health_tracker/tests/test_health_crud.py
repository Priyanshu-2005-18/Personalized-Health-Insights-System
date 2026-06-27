"""
tests/test_health_crud.py
=========================
Full CRUD test suite for the health tracking module.
Covers create, read, update, delete, pagination, filters, and ownership.
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/health"
TODAY = str(date.today())
YESTERDAY = str(date.today() - timedelta(days=1))
LAST_WEEK = str(date.today() - timedelta(days=7))


# ─────────────────────────────────────────────────────────────────────────────
#  CREATE  (POST /health)
# ─────────────────────────────────────────────────────────────────────────────

async def test_create_full_entry(client: AsyncClient, alice_headers: dict):
    resp = await client.post(BASE, headers=alice_headers, json={
        "entry_date": TODAY,
        "sleep_hours": 7.5,
        "steps": 9200,
        "calories_consumed": 2100,
        "water_intake_ml": 2500,
        "stress_level": 3,
        "heart_rate_bpm": 65,
        "notes": "Good day overall",
        "source": "manual",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["sleep_hours"] == 7.5
    assert data["steps"] == 9200
    assert data["calories_consumed"] == 2100
    assert data["water_intake_ml"] == 2500
    assert data["stress_level"] == 3
    assert data["heart_rate_bpm"] == 65
    # Computed fields
    assert data["sleep_minutes"] == 450          # 7.5h × 60
    assert data["water_intake_glasses"] == 10.0  # 2500 / 250
    assert data["stress_label"] == "Mild"
    assert "Excellent" in data["heart_rate_zone"]
    assert "password" not in data


async def test_create_partial_entry_sleep_only(client: AsyncClient, alice_headers: dict):
    """At least one metric is enough — all others can be omitted."""
    resp = await client.post(BASE, headers=alice_headers, json={
        "entry_date": YESTERDAY,
        "sleep_hours": 6.0,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["sleep_hours"] == 6.0
    assert data["steps"] is None
    assert data["calories_consumed"] is None


async def test_create_duplicate_date_returns_409(client: AsyncClient, alice_headers: dict):
    """Second entry for the same date must fail."""
    payload = {"entry_date": LAST_WEEK, "steps": 5000}
    r1 = await client.post(BASE, headers=alice_headers, json=payload)
    assert r1.status_code == 201
    r2 = await client.post(BASE, headers=alice_headers, json=payload)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"].lower()


async def test_create_no_metrics_returns_422(client: AsyncClient, alice_headers: dict):
    """Submitting with no metric data must be rejected."""
    resp = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-01-10",
        "notes": "Just a note, no metrics",
    })
    assert resp.status_code == 422


async def test_create_requires_auth(client: AsyncClient):
    resp = await client.post(BASE, json={"entry_date": TODAY, "steps": 1000})
    assert resp.status_code == 401


# ── Boundary validation ───────────────────────────────────────────────────────

@pytest.mark.parametrize("field,value", [
    ("sleep_hours", 25.0),       # > 24
    ("sleep_hours", -1.0),       # < 0
    ("steps", -1),               # < 0
    ("steps", 100_001),          # > 100 000
    ("calories_consumed", -1),   # < 0
    ("calories_consumed", 10_001),
    ("water_intake_ml", -1),
    ("water_intake_ml", 10_001),
    ("stress_level", 0),         # < 1
    ("stress_level", 11),        # > 10
    ("heart_rate_bpm", 29),      # < 30
    ("heart_rate_bpm", 251),     # > 250
])
async def test_create_out_of_range_rejected(
    client: AsyncClient, alice_headers: dict, field: str, value
):
    payload = {"entry_date": "2025-02-01", field: value}
    resp = await client.post(BASE, headers=alice_headers, json=payload)
    assert resp.status_code == 422, f"{field}={value} should fail"


@pytest.mark.parametrize("field,value", [
    ("sleep_hours", 0.0),
    ("sleep_hours", 24.0),
    ("steps", 0),
    ("steps", 100_000),
    ("stress_level", 1),
    ("stress_level", 10),
    ("heart_rate_bpm", 30),
    ("heart_rate_bpm", 250),
])
async def test_create_boundary_values_accepted(
    client: AsyncClient, alice_headers: dict, field: str, value
):
    """Exact boundary values (min and max) must be accepted."""
    d = f"2025-03-{str(abs(hash(field + str(value))) % 28 + 1).zfill(2)}"
    payload = {"entry_date": d, field: value}
    resp = await client.post(BASE, headers=alice_headers, json=payload)
    assert resp.status_code in (201, 409), f"{field}={value} failed with {resp.status_code}"


# ─────────────────────────────────────────────────────────────────────────────
#  READ — GET /health (list)
# ─────────────────────────────────────────────────────────────────────────────

async def test_list_returns_only_own_entries(
    client: AsyncClient, alice_headers: dict, bob_headers: dict
):
    await client.post(BASE, headers=alice_headers, json={"entry_date": "2024-06-01", "steps": 8000})
    await client.post(BASE, headers=bob_headers,  json={"entry_date": "2024-06-01", "steps": 4000})

    alice_list = await client.get(BASE, headers=alice_headers)
    bob_list   = await client.get(BASE, headers=bob_headers)

    alice_ids = {e["id"] for e in alice_list.json()["items"]}
    bob_ids   = {e["id"] for e in bob_list.json()["items"]}
    assert alice_ids.isdisjoint(bob_ids), "Users must not see each other's entries"


async def test_list_pagination(client: AsyncClient, alice_headers: dict):
    # Seed 5 entries on distinct dates
    for i in range(10, 15):
        d = f"2024-07-{i:02d}"
        r = await client.post(BASE, headers=alice_headers, json={"entry_date": d, "steps": i * 100})
        assert r.status_code in (201, 409)

    resp = await client.get(BASE, headers=alice_headers, params={"page": 1, "size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 2
    assert "total" in data
    assert "pages" in data
    assert data["size"] == 2


async def test_list_date_range_filter(client: AsyncClient, alice_headers: dict):
    resp = await client.get(BASE, headers=alice_headers, params={
        "start_date": "2024-07-10",
        "end_date": "2024-07-12",
    })
    assert resp.status_code == 200
    for entry in resp.json()["items"]:
        assert "2024-07-10" <= entry["entry_date"] <= "2024-07-12"


async def test_list_filter_by_min_steps(client: AsyncClient, alice_headers: dict):
    resp = await client.get(BASE, headers=alice_headers, params={"min_steps": 1200})
    for entry in resp.json()["items"]:
        if entry["steps"] is not None:
            assert entry["steps"] >= 1200


async def test_list_filter_by_max_stress(client: AsyncClient, alice_headers: dict):
    await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-08-01", "stress_level": 2
    })
    await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-08-02", "stress_level": 9
    })
    resp = await client.get(BASE, headers=alice_headers, params={"max_stress_level": 4})
    for entry in resp.json()["items"]:
        if entry["stress_level"] is not None:
            assert entry["stress_level"] <= 4


async def test_list_newest_first(client: AsyncClient, alice_headers: dict):
    resp = await client.get(BASE, headers=alice_headers)
    dates = [e["entry_date"] for e in resp.json()["items"]]
    assert dates == sorted(dates, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
#  READ — GET /health/today
# ─────────────────────────────────────────────────────────────────────────────

async def test_get_today_found(client: AsyncClient, alice_headers: dict):
    await client.post(BASE, headers=alice_headers, json={
        "entry_date": TODAY, "sleep_hours": 8.0
    })
    resp = await client.get(f"{BASE}/today", headers=alice_headers)
    assert resp.status_code == 200
    assert resp.json()["entry_date"] == TODAY


async def test_get_today_not_found(client: AsyncClient, bob_headers: dict):
    # Bob hasn't logged today
    resp = await client.get(f"{BASE}/today", headers=bob_headers)
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
#  READ — GET /health/date/{date}
# ─────────────────────────────────────────────────────────────────────────────

async def test_get_by_date_found(client: AsyncClient, alice_headers: dict):
    d = "2024-09-15"
    await client.post(BASE, headers=alice_headers, json={"entry_date": d, "steps": 7777})
    resp = await client.get(f"{BASE}/date/{d}", headers=alice_headers)
    assert resp.status_code == 200
    assert resp.json()["steps"] == 7777


async def test_get_by_date_not_found(client: AsyncClient, alice_headers: dict):
    resp = await client.get(f"{BASE}/date/2000-01-01", headers=alice_headers)
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
#  READ — GET /health/{id}
# ─────────────────────────────────────────────────────────────────────────────

async def test_get_by_id(client: AsyncClient, alice_headers: dict):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-10-01", "heart_rate_bpm": 72
    })
    entry_id = cr.json()["id"]
    resp = await client.get(f"{BASE}/{entry_id}", headers=alice_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == entry_id


async def test_get_by_id_wrong_owner(
    client: AsyncClient, alice_headers: dict, bob_headers: dict
):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-10-02", "steps": 3000
    })
    entry_id = cr.json()["id"]
    resp = await client.get(f"{BASE}/{entry_id}", headers=bob_headers)
    assert resp.status_code == 403


async def test_get_nonexistent_id(client: AsyncClient, alice_headers: dict):
    resp = await client.get(
        f"{BASE}/00000000-0000-0000-0000-000000000000", headers=alice_headers
    )
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
#  UPDATE  (PATCH /health/{id})
# ─────────────────────────────────────────────────────────────────────────────

async def test_patch_single_field(client: AsyncClient, alice_headers: dict):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-11-01",
        "sleep_hours": 6.0,
        "steps": 4000,
    })
    entry_id = cr.json()["id"]

    resp = await client.patch(
        f"{BASE}/{entry_id}", headers=alice_headers,
        json={"steps": 9999}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["steps"] == 9999
    assert data["sleep_hours"] == 6.0   # unchanged


async def test_patch_all_metrics(client: AsyncClient, alice_headers: dict):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-11-05", "steps": 1000
    })
    entry_id = cr.json()["id"]

    resp = await client.patch(f"{BASE}/{entry_id}", headers=alice_headers, json={
        "sleep_hours": 8.5,
        "steps": 12000,
        "calories_consumed": 1800,
        "water_intake_ml": 3000,
        "stress_level": 2,
        "heart_rate_bpm": 58,
        "notes": "Updated notes",
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["sleep_hours"] == 8.5
    assert d["steps"] == 12000
    assert d["stress_label"] == "Low"


async def test_patch_empty_body_returns_422(client: AsyncClient, alice_headers: dict):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-11-10", "steps": 2000
    })
    entry_id = cr.json()["id"]
    resp = await client.patch(f"{BASE}/{entry_id}", headers=alice_headers, json={})
    assert resp.status_code == 422


async def test_patch_wrong_owner(
    client: AsyncClient, alice_headers: dict, bob_headers: dict
):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-11-15", "steps": 5000
    })
    entry_id = cr.json()["id"]
    resp = await client.patch(
        f"{BASE}/{entry_id}", headers=bob_headers, json={"steps": 1}
    )
    assert resp.status_code == 403


async def test_patch_out_of_range_rejected(client: AsyncClient, alice_headers: dict):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-11-20", "steps": 5000
    })
    entry_id = cr.json()["id"]
    resp = await client.patch(
        f"{BASE}/{entry_id}", headers=alice_headers,
        json={"stress_level": 15}
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
#  DELETE
# ─────────────────────────────────────────────────────────────────────────────

async def test_delete_own_entry(client: AsyncClient, alice_headers: dict):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-12-01", "steps": 6000
    })
    entry_id = cr.json()["id"]

    del_resp = await client.delete(f"{BASE}/{entry_id}", headers=alice_headers)
    assert del_resp.status_code == 200
    assert "deleted" in del_resp.json()["message"].lower()

    get_resp = await client.get(f"{BASE}/{entry_id}", headers=alice_headers)
    assert get_resp.status_code == 404


async def test_delete_wrong_owner(
    client: AsyncClient, alice_headers: dict, bob_headers: dict
):
    cr = await client.post(BASE, headers=alice_headers, json={
        "entry_date": "2024-12-05", "steps": 6000
    })
    entry_id = cr.json()["id"]
    resp = await client.delete(f"{BASE}/{entry_id}", headers=bob_headers)
    assert resp.status_code == 403


async def test_delete_nonexistent(client: AsyncClient, alice_headers: dict):
    resp = await client.delete(
        f"{BASE}/00000000-0000-0000-0000-000000000000", headers=alice_headers
    )
    assert resp.status_code == 404
