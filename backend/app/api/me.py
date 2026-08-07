from fastapi import APIRouter, Depends

from app.auth import Principal, get_current_principal

router = APIRouter(prefix="/v1", tags=["identity"])


@router.get("/me", response_model=Principal)
def get_me(principal: Principal = Depends(get_current_principal)) -> Principal:
    return principal
