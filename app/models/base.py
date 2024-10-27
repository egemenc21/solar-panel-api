from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.time(datetime.timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
        
    # Method to update the timestamp automatically
    def update_timestamp(self):
        self.updated_at = datetime.now(datetime.timezone.utc)