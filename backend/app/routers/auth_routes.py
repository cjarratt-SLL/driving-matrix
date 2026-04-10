from fastapi import APIRouter

from app.auth import get_auth_policy

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/policy")
def auth_policy():
    return get_auth_policy()
