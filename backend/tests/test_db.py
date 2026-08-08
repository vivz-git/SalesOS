import pytest
import sys
import asyncio
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.db import get_db_session, tenant_transaction_context

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

pytestmark = pytest.mark.asyncio

async def test_tenant_transaction_context():
    # Generate mock UUIDs
    user_id = uuid4()
    workspace_id = uuid4()

    # Get a session
    session_generator = get_db_session()
    session = await anext(session_generator)

    try:
        # Wrap the session with the transaction context
        async with tenant_transaction_context(session, user_id, workspace_id) as ctx_session:
            # Check context variables are correctly set
            result = await ctx_session.execute(text("SELECT current_setting('salesos.app_user_id', true);"))
            app_user_id = result.scalar()
            assert app_user_id == str(user_id), "User ID context should be established"

            result = await ctx_session.execute(text("SELECT current_setting('salesos.app_workspace_id', true);"))
            app_workspace_id = result.scalar()
            assert app_workspace_id == str(workspace_id), "Workspace ID context should be established"

            # Force a rollback so we don't commit anything (even though no data was written)
            await ctx_session.rollback()
    except OperationalError as e:
        pytest.skip(f"Real PostgreSQL database is unavailable. Skipping integration test. Error: {e}")
    finally:
        await session.close()
