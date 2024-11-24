from datetime import datetime, timedelta, timezone
from typing import Annotated, Union
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database import get_session
from app.models.user import User
from app.services.auth import ACCESS_TOKEN_EXPIRE_MINUTES, Token, UserCreate, UserInDB, authenticate_user, create_access_token, get_user, hash_password

# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "full_name": "John Doe",
#         "email": "johndoe@example.com",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
#         "disabled": False,
#     }
# }


class LoginRequest(BaseModel):
    username: str
    password: str


router = APIRouter()


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    # login_request: LoginRequest,
    session: Session = Depends(get_session),
) -> Token:
    user = authenticate_user(session, form_data.username, str(form_data.password))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# Registering a new user
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, session: Session = Depends(get_session)):
    # Check if the username already exists in the database
    # existing_user = get_user(session, user.username)
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Username already registered"
    #     )

    # # Check if the email already exists
    # existing_email = session.exec(select(User).filter(User.email == user.email)).one_or_none()
    # if existing_email:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )

    # Hash the user's password before storing
    hashed_password = hash_password(str(user.password))

    # Create a new UserInDB instance and save it to the database
    db_user = User(
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        role=user.role,
        hashed_password=hashed_password
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user
