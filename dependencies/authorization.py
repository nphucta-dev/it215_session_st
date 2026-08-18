from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status

from dependencies.authentication import get_current_user
from models.models import User


class RoleChecker:
    def __init__(self, allowed_roles: set[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user


require_admin = RoleChecker({"admin"})


def require_owner_or_admin(owner_id: int, current_user: User) -> None:
    if current_user.role != "admin" and current_user.id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this resource")
