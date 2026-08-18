from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.authentication import get_current_user
from dependencies.authorization import require_admin, require_owner_or_admin
from models.models import Resource, User
from schemas.schemas import ResourceCreate, ResourceRead, ResourceUpdate
from services.resource_service import create_resource, delete_resource, get_resource_or_404, update_resource

router = APIRouter(prefix="/api/v1/resources", tags=["Learning Resources"])


@router.get("", response_model=list[ResourceRead])
def list_my_resources(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if current_user.role == "admin":
        return db.scalars(select(Resource).order_by(Resource.id)).all()
    return db.scalars(select(Resource).where(Resource.owner_id == current_user.id).order_by(Resource.id)).all()


@router.get("/{resource_id}", response_model=ResourceRead)
def get_resource(
    resource_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    resource = get_resource_or_404(db, resource_id)
    require_owner_or_admin(resource.owner_id, current_user)
    return resource


@router.post("", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
def create_learning_resource(
    payload: ResourceCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
):
    return create_resource(db, payload)


@router.patch("/{resource_id}", response_model=ResourceRead)
def update_learning_resource(
    resource_id: int,
    payload: ResourceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    resource = get_resource_or_404(db, resource_id)
    require_owner_or_admin(resource.owner_id, current_user)
    return update_resource(db, resource, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_learning_resource(
    resource_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
):
    resource = get_resource_or_404(db, resource_id)
    delete_resource(db, resource)
    return None
