from dataclasses import dataclass
from enum import Enum

from fastapi import Depends, HTTPException, Request, status


class UserRole(str, Enum):
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    VIEWER = "viewer"
    READ_ONLY = "read_only"


DEFAULT_ROLE = UserRole.VIEWER
TRIP_MUTATION_ROLES = (UserRole.ADMIN, UserRole.DISPATCHER)


@dataclass(frozen=True)
class AuthUser:
    user_id: str
    role: UserRole


async def auth_context_middleware(request: Request, call_next):
    user_id = request.headers.get("x-user-id")
    role_value = request.headers.get("x-user-role", DEFAULT_ROLE.value).lower().strip()

    try:
        role = UserRole(role_value)
    except ValueError:
        role = DEFAULT_ROLE

    request.state.auth_user = AuthUser(user_id=user_id or "anonymous", role=role)
    return await call_next(request)


def get_current_user(request: Request) -> AuthUser:
    auth_user = getattr(request.state, "auth_user", None)
    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication context missing",
        )

    if auth_user.user_id == "anonymous":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return auth_user


def require_trip_mutation_role(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role not in TRIP_MUTATION_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for trip mutation",
        )

    return user


def get_auth_policy() -> dict[str, list[str] | str]:
    return {
        "default_role": DEFAULT_ROLE.value,
        "trip_mutation_roles": [role.value for role in TRIP_MUTATION_ROLES],
    }
