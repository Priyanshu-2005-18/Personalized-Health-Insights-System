from app.db.base import Base
from app.db.session import engine

# Import models so Base.metadata picks them up
from app.models import user  # noqa: F401


async def init_db() -> None:
    """Create all tables that don't already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
