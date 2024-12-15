from typing import List
from sqlmodel import Field, Relationship
from .base import BaseModel
from typing import Optional
from datetime import datetime
class User(BaseModel, table=True):
    username: str = Field(index=True, nullable=False, unique=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    role: str  # e.g., 'owner', 'worker', 'drone_operator'

    # Forward references for circular imports
    fields: List['SolarField'] = Relationship(back_populates="user")
    jobs: List['Job'] = Relationship(back_populates="owner")


class SolarField(BaseModel, table=True):
    name: str = Field(index=True)
    location: str  # e.g., New York, Ankara
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Use type hints instead of direct imports
    user: Optional['User'] = Relationship()
    images: List['PanelImage'] = Relationship()


class PanelImage(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str  # Path to the classified image
    field_id: Optional[int] = Field(default=None, foreign_key="solarfield.id")
    
    # Relationships
    field: Optional[SolarField] = Relationship(back_populates="images")
    image_class: str # 'clean', 'dirty', 'damaged'

class Job(BaseModel, table=True):
    description: str
    location: str
    # e.g., 1:'pending', 2:'in_progress', 3:'completed'
    status: int = Field(default=1)
    # Link to thermal images uploaded by the user
    image_url: Optional[str] = None

    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional["User"] = Relationship(back_populates="jobs")