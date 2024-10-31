from sqlmodel import Field, Relationship
from typing import Optional
from app.models.base import BaseModel

class Job(BaseModel, table=True):
    description: str
    location: str
    status: int = Field(default=1)  # e.g., 1:'pending', 2:'in_progress', 3:'completed'
    image_url: Optional[str] = None  # Link to thermal images uploaded by the user

    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional["User"] = Relationship(back_populates="jobs")