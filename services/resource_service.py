from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import Resource, User
from schemas.schemas import ResourceCreate, ResourceUpdate


def get_resource_or_404(db: Session, resource_id: int) -> Resource:
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


def create_resource(db: Session, payload: ResourceCreate) -> Resource:
    owner = db.get(User, payload.owner_id)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found")
    if not owner.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner account is inactive")
    resource = Resource(**payload.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def update_resource(db: Session, resource: Resource, payload: ResourceUpdate) -> Resource:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(resource, key, value)
    db.commit()
    db.refresh(resource)
    return resource


def delete_resource(db: Session, resource: Resource) -> None:
    db.delete(resource)
    db.commit()
