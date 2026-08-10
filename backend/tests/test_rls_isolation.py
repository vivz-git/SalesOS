import asyncio
import sys
from typing import Any, cast
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import get_db_session, tenant_transaction_context

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

pytestmark = pytest.mark.asyncio



@pytest_asyncio.fixture
async def two_workspaces() -> Any:
    admin_engine = create_async_engine("postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres")
    
    ws1_id = uuid4()
    ws2_id = uuid4()
    user1_id = uuid4()
    user2_id = uuid4()
    
    try:
        async with admin_engine.begin() as conn:
            # Create User 1 and Workspace 1
            await conn.execute(
                text("INSERT INTO auth.users (id, instance_id, aud, role, email) VALUES (:uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', :email)"),
                {"uid": str(user1_id), "email": f"rls1_{user1_id}@example.com"}
            )
            await conn.execute(
                text("INSERT INTO workspaces (id, name, slug) VALUES (:wid, 'Workspace 1', :slug)"),
                {"wid": str(ws1_id), "slug": f"rls-ws1-{ws1_id}"}
            )
            await conn.execute(
                text("INSERT INTO memberships (id, workspace_id, user_id, role, created_at, updated_at) VALUES (:mid, :wid, :uid, 'owner', now(), now())"),
                {"mid": str(uuid4()), "wid": str(ws1_id), "uid": str(user1_id)}
            )
            
            # Create User 2 and Workspace 2
            await conn.execute(
                text("INSERT INTO auth.users (id, instance_id, aud, role, email) VALUES (:uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', :email)"),
                {"uid": str(user2_id), "email": f"rls2_{user2_id}@example.com"}
            )
            await conn.execute(
                text("INSERT INTO workspaces (id, name, slug) VALUES (:wid, 'Workspace 2', :slug)"),
                {"wid": str(ws2_id), "slug": f"rls-ws2-{ws2_id}"}
            )
            await conn.execute(
                text("INSERT INTO memberships (id, workspace_id, user_id, role, created_at, updated_at) VALUES (:mid, :wid, :uid, 'owner', now(), now())"),
                {"mid": str(uuid4()), "wid": str(ws2_id), "uid": str(user2_id)}
            )
            
        yield {"ws1": ws1_id, "ws2": ws2_id, "u1": user1_id, "u2": user2_id}
        
    finally:
        await admin_engine.dispose()



async def test_rls_cross_workspace_isolation(two_workspaces: Any) -> None:
    ws1 = two_workspaces["ws1"]
    ws2 = two_workspaces["ws2"]
    u1 = two_workspaces["u1"]
    u2 = two_workspaces["u2"]
    
    # We use the unprivileged salesos_backend session
    session_generator = get_db_session()
    session = await anext(session_generator)
    
    try:
        # 1. As ws2, create a campaign
        camp2_id = uuid4()
        async with tenant_transaction_context(session, u2, ws2) as ctx:
            await ctx.execute(
                text("INSERT INTO campaigns (id, workspace_id, name, created_by, status) VALUES (:id, :wid, 'Camp 2', :uid, 'draft')"),
                {"id": str(camp2_id), "wid": str(ws2), "uid": str(u2)}
            )
            # The context manager automatically flushes/commits when exiting

        # 2. Try cross-workspace SELECT
        async with tenant_transaction_context(session, u1, ws1) as ctx:
            result = await ctx.execute(
                text("SELECT id FROM campaigns WHERE id = :id"),
                {"id": str(camp2_id)}
            )
            row = result.fetchone()
            assert row is None, "SELECT isolation failed: ws1 could read ws2's campaign"
            
        # 3. Try cross-workspace INSERT
        camp_invalid_id = uuid4()
        with pytest.raises(ProgrammingError) as exc_info:
            async with tenant_transaction_context(session, u1, ws1) as ctx:
                await ctx.execute(
                    text("INSERT INTO campaigns (id, workspace_id, name, created_by, status) VALUES (:id, :wid, 'Camp Invalid', :uid, 'draft')"),
                    {"id": str(camp_invalid_id), "wid": str(ws2), "uid": str(u1)}
                )
        assert "insufficientprivilege" in str(exc_info.value).lower() or "row-level security" in str(exc_info.value).lower(), "INSERT isolation failed: ws1 could insert a campaign into ws2"
        
        # 4. Try cross-workspace UPDATE
        async with tenant_transaction_context(session, u1, ws1) as ctx:
            result = await ctx.execute(
                text("UPDATE campaigns SET name = 'Hacked' WHERE id = :id"),
                {"id": str(camp2_id)}
            )
            assert cast(Any, result).rowcount == 0, "UPDATE isolation failed: ws1 could update ws2's campaign"
            
        # 5. Try cross-workspace DELETE
        async with tenant_transaction_context(session, u1, ws1) as ctx:
            result = await ctx.execute(
                text("DELETE FROM campaigns WHERE id = :id"),
                {"id": str(camp2_id)}
            )
            assert cast(Any, result).rowcount == 0, "DELETE isolation failed: ws1 could delete ws2's campaign"
            
    finally:
        await session.close()
