import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.accounts import router as accounts_router
from app.api.approvals import router as approvals_router
from app.api.campaigns import router as campaigns_router
from app.api.contacts import router as contacts_router
from app.api.conversations import router as conversations_router
from app.api.deliveries import router as deliveries_router
from app.api.health import router as health_router
from app.api.hubspot import router as hubspot_router
from app.api.me import router as me_router
from app.api.outreach import router as outreach_router
from app.api.reports import router as reports_router
from app.api.research import router as research_router
from app.api.sequences import router as sequences_router
from app.api.workspaces import router as workspaces_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import engine
from app.worker import process_jobs


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    worker_task = None
    if os.environ.get("TESTING") != "1":
        worker_task = asyncio.create_task(process_jobs())
    yield
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    await engine.dispose()


app = FastAPI(
    title="SalesOS API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

settings = get_settings()
raw_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
origins = [o for o in raw_origins if o != "*"]
if not origins:
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(me_router)
app.include_router(workspaces_router)
app.include_router(campaigns_router)
app.include_router(accounts_router)
app.include_router(contacts_router)
app.include_router(research_router)
app.include_router(outreach_router)
app.include_router(approvals_router)
app.include_router(deliveries_router)
app.include_router(conversations_router)
app.include_router(sequences_router)
app.include_router(hubspot_router)
app.include_router(reports_router)

