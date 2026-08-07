from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


@router.get("/health", response_model=HealthResponse, include_in_schema=False)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
