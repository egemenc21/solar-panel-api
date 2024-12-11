from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import Annotated, List, Optional
from app.database import get_session
from app.models.models import SolarField, PanelImage
from app.services.auth import User, get_current_active_user
router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

# CRUD operations for PanelImages


@router.post("/", response_model=PanelImage, status_code=status.HTTP_201_CREATED)
def create_panel_image(session: SessionDep, image: PanelImage, current_user: Annotated[User, Depends(get_current_active_user)]):
    session.add(image)
    session.commit()
    session.refresh(image)
    return image


@router.get("/", response_model=List[PanelImage])
def read_panel_images(session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]):
    images = session.exec(select(PanelImage)).all()
    return images


@router.get("/{image_id}", response_model=PanelImage)
def read_panel_image(session: SessionDep, image_id: int, current_user: Annotated[User, Depends(get_current_active_user)]):
    image = session.get(PanelImage, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PanelImage not found")
    return image


@router.put("/{image_id}", response_model=PanelImage )
def update_panel_image(session: SessionDep, image_id: int, image: PanelImage, current_user: Annotated[User, Depends(get_current_active_user)]):
    db_image = session.get(PanelImage, image_id)
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PanelImage not found")
    image_data = image.dict(exclude_unset=True)
    for key, value in image_data.items():
        setattr(db_image, key, value)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_panel_image(session: SessionDep, image_id: int, current_user: Annotated[User, Depends(get_current_active_user)]):
    image = session.get(PanelImage, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PanelImage not found")
    session.delete(image)
    session.commit()
    return {"ok": True}
