import asyncio
import os
import sys
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

os.environ["TESTING"] = "1"

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def event_loop() -> Any:
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def seeded_workspace() -> Any:
    from sqlalchemy.ext.asyncio import create_async_engine

    workspace_id = uuid4()
    user_id = uuid4()
    campaign_id = uuid4()

    # Use superuser with short connection timeout to fail fast if local db is absent
    admin_engine = create_async_engine(
        "postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres",
        pool_size=1,
        connect_args={"connect_timeout": 1},
    )

    try:
        async with asyncio.timeout(2.0):
            async with admin_engine.begin() as conn:
                # Insert into auth.users to satisfy foreign keys
                await conn.execute(
                    text(
                        "INSERT INTO auth.users (id, instance_id, aud, role, email) "
                        "VALUES (:uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', :email)"
                    ),
                    {"uid": str(user_id), "email": f"test_{user_id}@example.com"},
                )
                await conn.execute(
                    text("INSERT INTO workspaces (id, name, slug) VALUES (:wid, 'Integration Workspace', :slug)"),
                    {"wid": str(workspace_id), "slug": f"test-workspace-{workspace_id}"},
                )
                await conn.execute(
                    text(
                        "INSERT INTO campaigns (id, workspace_id, name, status, created_by, target_segment, icp_definition) "
                        "VALUES (:cid, :wid, 'Test Campaign', 'active', :uid, 'segment', 'icp')"
                    ),
                    {"cid": str(campaign_id), "wid": str(workspace_id), "uid": str(user_id)},
                )
                await conn.execute(
                    text(
                        "INSERT INTO memberships (id, workspace_id, user_id, role, created_at, updated_at) "
                        "VALUES (:mid, :wid, :uid, 'owner', now(), now())"
                    ),
                    {"mid": str(uuid4()), "wid": str(workspace_id), "uid": str(user_id)},
                )
    except Exception as e:
        pytest.skip(f"Live PostgreSQL at 127.0.0.1:54322 is unavailable: {e}")
    finally:
        await admin_engine.dispose()

    yield workspace_id, user_id
