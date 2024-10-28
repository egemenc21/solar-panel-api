from typing import Annotated
from fastapi import APIRouter, Depends
from routers.auth import User, get_current_active_user

router = APIRouter()

@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user