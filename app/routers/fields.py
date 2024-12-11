from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import Annotated, List
from app.database import get_session
from app.models.models import SolarField
from app.services.auth import User, get_current_active_user

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

@router.post("/", response_model=SolarField, status_code=status.HTTP_201_CREATED)
def create_field(session: SessionDep, field: SolarField, current_user: Annotated[User, Depends(get_current_active_user)]):
    session.add(field)
    session.commit()
    session.refresh(field)
    return field

@router.get("/", response_model=List[SolarField])
def read_fields(session:SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]):
    fields = session.exec(select(SolarField)).all()
    return fields

@router.get("/{field_id}", response_model=SolarField)
def read_field(session: SessionDep, field_id: int, current_user: Annotated[User, Depends(get_current_active_user)]):
    field = session.get(SolarField, field_id)
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SolarField not found")
    return field

@router.put("/{field_id}", response_model=SolarField)
def update_field(session:SessionDep, field_id: int, field: SolarField, current_user: Annotated[User, Depends(get_current_active_user)]):
    db_field = session.get(SolarField, field_id)
    if not db_field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SolarField not found")
    field_data = field.dict(exclude_unset=True)
    for key, value in field_data.items():
        setattr(db_field, key, value)
    db_field.update_timestamp()
    session.add(db_field)
    session.commit()
    session.refresh(db_field)
    return db_field

@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field(field_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]):
    field = session.get(SolarField, field_id)
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SolarField not found")
    session.delete(field)
    session.commit()
    return {"ok": True}
