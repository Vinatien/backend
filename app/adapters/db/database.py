"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.utils.settings import DATABASE_URL

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)


async def get_session() -> AsyncSession:
    """
    Get database session dependency for FastAPI.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()