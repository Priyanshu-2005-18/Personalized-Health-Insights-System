"""
services/health_service.py
==========================
All business logic for health entry CRUD and analytics.

Methods:
  create        — insert new entry (enforces one-per-day rule)
  get_by_id     — fetch single entry by UUID
  get_by_date   — fetch entry for a specific calendar date
  list_entries  — paginated list with optional date-range + metric filters
  update        — partial update (PATCH semantics)
  delete        — hard delete
  get_summary   — aggregate statistics over a date range
  get_streak    — current consecutive-day logging streak
"""

import math
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.health_entry import HealthEntry
from app.schemas.health_entry import (
    HealthEntryCreate,
    HealthEntryRead,
    HealthEntryUpdate,
    HealthSummary,
    PaginatedHealthEntries,
)


class HealthService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    #  CREATE
    # ─────────────────────────────────────────────────────────────────────────

    async def create(self, user_id: UUID, payload: HealthEntryCreate) -> HealthEntryRead:
        """
        Create a health entry for the given date.
        Raises 409 if an entry for that date already exists.
        """
        existing = await self._get_by_date_raw(user_id, payload.entry_date)
        if existing:
            raise ConflictException(
                f"A health entry for {payload.entry_date} already exists. "
                "Use PATCH to update it."
            )

        entry = HealthEntry(
            user_id=user_id,
            **payload.model_dump(),
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return HealthEntryRead.from_orm_with_computed(entry)

    # ─────────────────────────────────────────────────────────────────────────
    #  READ — single
    # ─────────────────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: UUID, entry_id: UUID) -> HealthEntryRead:
        """Fetch a single entry by UUID. Enforces ownership."""
        entry = await self.db.get(HealthEntry, entry_id)
        if not entry:
            raise NotFoundException("Health entry")
        if entry.user_id != user_id:
            raise ForbiddenException("You do not own this health entry")
        return HealthEntryRead.from_orm_with_computed(entry)

    async def get_by_date(self, user_id: UUID, entry_date: date) -> HealthEntryRead:
        """Fetch the entry for a specific calendar date."""
        entry = await self._get_by_date_raw(user_id, entry_date)
        if not entry:
            raise NotFoundException(f"Health entry for {entry_date}")
        return HealthEntryRead.from_orm_with_computed(entry)

    # ─────────────────────────────────────────────────────────────────────────
    #  READ — list with pagination + filters
    # ─────────────────────────────────────────────────────────────────────────

    async def list_entries(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_sleep_hours: Optional[float] = None,
        max_stress_level: Optional[int] = None,
        min_steps: Optional[int] = None,
        source: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedHealthEntries:
        """
        Paginated, filtered list of entries for a user.
        Returns entries newest-first.
        """
        query = select(HealthEntry).where(HealthEntry.user_id == user_id)

        # ── Optional filters ──────────────────────────────────────────────────
        if start_date:
            query = query.where(HealthEntry.entry_date >= start_date)
        if end_date:
            query = query.where(HealthEntry.entry_date <= end_date)
        if min_sleep_hours is not None:
            query = query.where(HealthEntry.sleep_hours >= min_sleep_hours)
        if max_stress_level is not None:
            query = query.where(HealthEntry.stress_level <= max_stress_level)
        if min_steps is not None:
            query = query.where(HealthEntry.steps >= min_steps)
        if source:
            query = query.where(HealthEntry.source == source)

        # ── Total count ───────────────────────────────────────────────────────
        count_q = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_q) or 0

        # ── Paginate ──────────────────────────────────────────────────────────
        offset = (page - 1) * size
        rows = await self.db.scalars(
            query.order_by(HealthEntry.entry_date.desc()).limit(size).offset(offset)
        )
        items = [HealthEntryRead.from_orm_with_computed(e) for e in rows.all()]

        return PaginatedHealthEntries(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=max(1, math.ceil(total / size)),
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  UPDATE  (PATCH)
    # ─────────────────────────────────────────────────────────────────────────

    async def update(
        self, user_id: UUID, entry_id: UUID, payload: HealthEntryUpdate
    ) -> HealthEntryRead:
        """
        Partial update — only supplied (non-None) fields are written.
        Ownership is checked before any mutation.
        """
        entry = await self.db.get(HealthEntry, entry_id)
        if not entry:
            raise NotFoundException("Health entry")
        if entry.user_id != user_id:
            raise ForbiddenException("You do not own this health entry")

        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        await self.db.commit()
        await self.db.refresh(entry)
        return HealthEntryRead.from_orm_with_computed(entry)

    # ─────────────────────────────────────────────────────────────────────────
    #  DELETE
    # ─────────────────────────────────────────────────────────────────────────

    async def delete(self, user_id: UUID, entry_id: UUID) -> None:
        """Hard delete. Raises 404/403 on not found or wrong owner."""
        entry = await self.db.get(HealthEntry, entry_id)
        if not entry:
            raise NotFoundException("Health entry")
        if entry.user_id != user_id:
            raise ForbiddenException("You do not own this health entry")

        await self.db.delete(entry)
        await self.db.commit()

    # ─────────────────────────────────────────────────────────────────────────
    #  ANALYTICS — summary
    # ─────────────────────────────────────────────────────────────────────────

    async def get_summary(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> HealthSummary:
        """
        Aggregate statistics over a date range.
        Uses SQL aggregation functions for efficiency — no Python-level iteration.
        """
        if start_date > end_date:
            from app.core.exceptions import BadRequestException
            raise BadRequestException("start_date must not be after end_date")

        result = await self.db.execute(
            select(
                func.count(HealthEntry.id).label("total"),
                # Sleep
                func.avg(HealthEntry.sleep_hours).label("avg_sleep"),
                func.min(HealthEntry.sleep_hours).label("min_sleep"),
                func.max(HealthEntry.sleep_hours).label("max_sleep"),
                # Steps
                func.avg(HealthEntry.steps).label("avg_steps"),
                func.sum(HealthEntry.steps).label("total_steps"),
                func.max(HealthEntry.steps).label("max_steps"),
                # Calories
                func.avg(HealthEntry.calories_consumed).label("avg_cal"),
                func.sum(HealthEntry.calories_consumed).label("total_cal"),
                # Water
                func.avg(HealthEntry.water_intake_ml).label("avg_water"),
                func.sum(HealthEntry.water_intake_ml).label("total_water"),
                # Stress
                func.avg(HealthEntry.stress_level).label("avg_stress"),
                func.min(HealthEntry.stress_level).label("min_stress"),
                func.max(HealthEntry.stress_level).label("max_stress"),
                # Heart rate
                func.avg(HealthEntry.heart_rate_bpm).label("avg_hr"),
                func.min(HealthEntry.heart_rate_bpm).label("min_hr"),
                func.max(HealthEntry.heart_rate_bpm).label("max_hr"),
            ).where(
                and_(
                    HealthEntry.user_id == user_id,
                    HealthEntry.entry_date >= start_date,
                    HealthEntry.entry_date <= end_date,
                )
            )
        )
        row = result.one()

        def _round(val, dp=2):
            return round(float(val), dp) if val is not None else None

        return HealthSummary(
            period_start=start_date,
            period_end=end_date,
            total_entries=row.total or 0,
            avg_sleep_hours=_round(row.avg_sleep),
            min_sleep_hours=_round(row.min_sleep),
            max_sleep_hours=_round(row.max_sleep),
            avg_steps=_round(row.avg_steps, 0),
            total_steps=int(row.total_steps) if row.total_steps else None,
            max_steps=int(row.max_steps) if row.max_steps else None,
            avg_calories_consumed=_round(row.avg_cal, 0),
            total_calories_consumed=int(row.total_cal) if row.total_cal else None,
            avg_water_intake_ml=_round(row.avg_water, 0),
            total_water_intake_ml=int(row.total_water) if row.total_water else None,
            avg_stress_level=_round(row.avg_stress),
            min_stress_level=int(row.min_stress) if row.min_stress else None,
            max_stress_level=int(row.max_stress) if row.max_stress else None,
            avg_heart_rate_bpm=_round(row.avg_hr),
            min_heart_rate_bpm=int(row.min_hr) if row.min_hr else None,
            max_heart_rate_bpm=int(row.max_hr) if row.max_hr else None,
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  ANALYTICS — streak
    # ─────────────────────────────────────────────────────────────────────────

    async def get_streak(self, user_id: UUID) -> dict:
        """
        Count the current consecutive-day logging streak ending today.
        Also returns the longest streak ever recorded.
        """
        rows = await self.db.scalars(
            select(HealthEntry.entry_date)
            .where(HealthEntry.user_id == user_id)
            .order_by(HealthEntry.entry_date.desc())
        )
        dates = sorted(rows.all(), reverse=True)

        if not dates:
            return {"current_streak": 0, "longest_streak": 0, "last_entry_date": None}

        # Current streak — must include today or yesterday
        today = date.today()
        current = 0
        if dates[0] >= today - timedelta(days=1):
            prev = dates[0]
            for d in dates:
                if (prev - d).days <= 1:
                    current += 1
                    prev = d
                else:
                    break

        # Longest streak ever
        longest = 1
        run = 1
        for i in range(1, len(dates)):
            if (dates[i - 1] - dates[i]).days == 1:
                run += 1
                longest = max(longest, run)
            else:
                run = 1

        return {
            "current_streak": current,
            "longest_streak": max(longest, current),
            "last_entry_date": str(dates[0]),
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  Internal helper
    # ─────────────────────────────────────────────────────────────────────────

    async def _get_by_date_raw(
        self, user_id: UUID, entry_date: date
    ) -> Optional[HealthEntry]:
        return await self.db.scalar(
            select(HealthEntry).where(
                HealthEntry.user_id == user_id,
                HealthEntry.entry_date == entry_date,
            )
        )
