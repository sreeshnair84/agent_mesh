"""
Database configuration and connection management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator
import logging

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Create async engine
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=10,
    pool_recycle=3600,
)

# Create sync session factory
SyncSessionLocal = sessionmaker(
    sync_engine,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


def get_sync_db():
    """
    Get synchronous database session
    """
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        db.close()


async def init_db():
    """
    Initialize database
    """
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created successfully")


async def close_db():
    """
    Close database connections
    """
    await engine.dispose()
    logging.info("Database connections closed")


# Database health check
async def check_db_health() -> bool:
    """
    Check database connection health
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        return False
