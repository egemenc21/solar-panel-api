from typing import Annotated
from fastapi import APIRouter, Depends
from services.auth import User, get_current_active_user

router = APIRouter()

@router.get("/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user