from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
import os

from sqlalchemy import text, NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}
if os.environ.get("TESTING") == "1":
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def tenant_transaction_context(
    session: AsyncSession, user_id: UUID, workspace_id: UUID
) -> AsyncGenerator[AsyncSession, None]:
    """
    Wraps an async session to ensure the transaction runs within a secure
    RLS and least-privilege boundary.
    """
    async with session.begin():
        # Inject RLS parameters local to the transaction (expires on commit/rollback)
        await session.execute(
            text("SELECT set_config('salesos.app_user_id', :user_id, true)"),
            {"user_id": str(user_id)},
        )
        await session.execute(
            text("SELECT set_config('salesos.app_workspace_id', :workspace_id, true)"),
            {"workspace_id": str(workspace_id)},
        )
        
        yield session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding standard async sessions."""
    async with AsyncSessionLocal() as session:
        yield session
