
from typing import List
from sqlmodel import Field, Relationship
from .base import BaseModel

class User(BaseModel, table=True):
    username: str = Field(index=True, nullable=False, unique=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    role: str  # e.g., 'owner', 'worker', 'drone_operator'

    jobs: List["Job"] = Relationship(back_populates="owner")