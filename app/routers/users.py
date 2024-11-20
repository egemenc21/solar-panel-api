from typing import Annotated, List
from fastapi import APIRouter, Depends
from app.services.auth import User, get_current_active_user
from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models.user import User

router = APIRouter()



@router.get("/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(session: SessionDep, user: User, current_user: Annotated[User, Depends(get_current_active_user)]):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/", response_model=List[User])
def read_users(session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]):
    users = session.exec(select(User)).all()
    return users


@router.get("/{user_id}", response_model=User)
def read_user(session: SessionDep, user_id: int, current_user: Annotated[User, Depends(get_current_active_user)]):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
def update_user(session: SessionDep, user_id: int, user: User, current_user: Annotated[User, Depends(get_current_active_user)]):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    user_data = user.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}
