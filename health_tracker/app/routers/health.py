"""
routers/health.py
=================
Health tracking REST API.

Endpoints:
  POST   /health              — log a new daily entry
  GET    /health              — list entries (paginated + filtered)
  GET    /health/today        — shortcut for today's entry
  GET    /health/summary      — aggregate statistics over a date range
  GET    /health/streak       — current + longest consecutive-day streak
  GET    /health/date/{date}  — entry for a specific calendar date
  GET    /health/{id}         — entry by UUID
  PATCH  /health/{id}         — partial update of an entry
  DELETE /health/{id}         — delete an entry
"""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DBSession
from app.models.user import User
from app.schemas.health_entry import (
    HealthEntryCreate,
    HealthEntryRead,
    HealthEntryUpdate,
    HealthSummary,
    MessageResponse,
    PaginatedHealthEntries,
)
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["Health Tracking"])


# ─────────────────────────────────────────────────────────────────────────────
#  POST — create
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=HealthEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log daily health metrics",
    description="""
Submit a health snapshot for a given date.

**Rules:**
- One entry per calendar date per user. Use `PATCH /health/{id}` to update.
- At least one metric must be supplied (all are optional individually).
- `entry_date` defaults to today if omitted.

**Metric constraints:**

| Metric | Min | Max | Unit |
|---|---|---|---|
| `sleep_hours` | 0.0 | 24.0 | hours (supports decimals, e.g. 7.5) |
| `steps` | 0 | 100 000 | steps/day |
| `calories_consumed` | 0 | 10 000 | kcal |
| `water_intake_ml` | 0 | 10 000 | ml |
| `stress_level` | 1 | 10 | 1 = no stress, 10 = extreme |
| `heart_rate_bpm` | 30 | 250 | bpm (resting) |
""",
)
async def create_entry(
    payload: HealthEntryCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> HealthEntryRead:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).create(user.id, payload)


# ─────────────────────────────────────────────────────────────────────────────
#  GET — list with pagination + filters
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedHealthEntries,
    summary="List health entries",
    description="""
Paginated list of all health entries for the current user, newest first.

Supports optional filters:
- **Date range** — `start_date` / `end_date` (inclusive, YYYY-MM-DD)
- **Min sleep** — only entries with `sleep_hours ≥ min_sleep_hours`
- **Max stress** — only entries with `stress_level ≤ max_stress_level`
- **Min steps** — only entries with `steps ≥ min_steps`
- **Source** — filter by data source (manual, fitbit, etc.)
""",
)
async def list_entries(
    current_user: CurrentUser,
    db: DBSession,
    start_date: Optional[date] = Query(None, description="Filter from date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter to date (inclusive)"),
    min_sleep_hours: Optional[float] = Query(None, ge=0, le=24),
    max_stress_level: Optional[int] = Query(None, ge=1, le=10),
    min_steps: Optional[int] = Query(None, ge=0),
    source: Optional[str] = Query(None, max_length=30),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Results per page"),
) -> PaginatedHealthEntries:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).list_entries(
        user_id=user.id,
        start_date=start_date,
        end_date=end_date,
        min_sleep_hours=min_sleep_hours,
        max_stress_level=max_stress_level,
        min_steps=min_steps,
        source=source,
        page=page,
        size=size,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  GET — today shortcut
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/today",
    response_model=HealthEntryRead,
    summary="Get today's health entry",
    description="Convenience shortcut — returns the entry for today's date. Returns 404 if not yet logged.",
)
async def get_today(current_user: CurrentUser, db: DBSession) -> HealthEntryRead:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).get_by_date(user.id, date.today())


# ─────────────────────────────────────────────────────────────────────────────
#  GET — summary analytics
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=HealthSummary,
    summary="Get aggregated health statistics",
    description="""
Returns aggregate statistics (avg, min, max, total) for all six metrics
over a given date range. Both `start_date` and `end_date` are **inclusive**.

Useful for building weekly/monthly progress reports.
""",
)
async def get_summary(
    current_user: CurrentUser,
    db: DBSession,
    start_date: date = Query(..., description="Range start (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Range end (YYYY-MM-DD)"),
) -> HealthSummary:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).get_summary(user.id, start_date, end_date)


# ─────────────────────────────────────────────────────────────────────────────
#  GET — streak
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/streak",
    summary="Get logging streak",
    description="""
Returns:
- **current_streak** — consecutive days logged up to today (or yesterday)
- **longest_streak** — longest consecutive run ever
- **last_entry_date** — most recent log date
""",
)
async def get_streak(current_user: CurrentUser, db: DBSession) -> dict:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).get_streak(user.id)


# ─────────────────────────────────────────────────────────────────────────────
#  GET — by specific date
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/date/{entry_date}",
    response_model=HealthEntryRead,
    summary="Get entry by calendar date",
    description="Fetch the health entry for an exact calendar date (YYYY-MM-DD).",
)
async def get_by_date(
    entry_date: date,
    current_user: CurrentUser,
    db: DBSession,
) -> HealthEntryRead:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).get_by_date(user.id, entry_date)


# ─────────────────────────────────────────────────────────────────────────────
#  GET — by UUID
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{entry_id}",
    response_model=HealthEntryRead,
    summary="Get entry by ID",
)
async def get_by_id(
    entry_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> HealthEntryRead:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).get_by_id(user.id, entry_id)


# ─────────────────────────────────────────────────────────────────────────────
#  PATCH — partial update
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/{entry_id}",
    response_model=HealthEntryRead,
    summary="Update a health entry",
    description="""
Partial update — supply only the fields you want to change.
All metric constraints apply exactly as in the POST endpoint.
Returns the full updated entry.
""",
)
async def update_entry(
    entry_id: UUID,
    payload: HealthEntryUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> HealthEntryRead:
    user: User = current_user  # type: ignore[assignment]
    return await HealthService(db).update(user.id, entry_id, payload)


# ─────────────────────────────────────────────────────────────────────────────
#  DELETE
# ─────────────────────────────────────────────────────────────────────────────

@router.delete(
    "/{entry_id}",
    response_model=MessageResponse,
    summary="Delete a health entry",
    description="Permanently delete an entry. This action cannot be undone.",
)
async def delete_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    user: User = current_user  # type: ignore[assignment]
    await HealthService(db).delete(user.id, entry_id)
    return MessageResponse(message="Health entry deleted successfully")
