from sqlmodel import Field, Relationship
from typing import Optional
from app.models.base import BaseModel
# Job Details: The Job model includes a status field to track the job’s progress, an optional image_url to store the location of thermal images, and links back to the user who created it.


class Job(BaseModel, table=True):
    description: str
    location: str
    # e.g., 1:'pending', 2:'in_progress', 3:'completed'
    status: int = Field(default=1)
    # Link to thermal images uploaded by the user
    image_url: Optional[str] = None

    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional["User"] = Relationship(back_populates="jobs")
    # A reference to the user who created the job, allowing us to easily access the user's details.
    # Real-Life Example
# Imagine you have a task management app where users can create tasks for themselves or others. Here's how it works:

# User: John creates a task to fix a broken solar panel.
# Job: The task (or job) has a description ("Fix the broken solar panel"), a location ("123 Solar St."), a status (1 for 'pending'), and an optional image link (a photo of the broken panel).
# Owner: John is the owner of this task, so his user ID is linked to the job.
