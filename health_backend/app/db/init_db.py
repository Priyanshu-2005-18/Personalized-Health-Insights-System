from app.db.session import engine
from app.db.base import Base

# Import all models so Base.metadata knows about them
from app.models import user, profile, health_log, sleep_log, activity_log  # noqa: F401
from app.models import nutrition_log, recommendation, notification          # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
