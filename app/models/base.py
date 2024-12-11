from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional

def utc_now():
    """Returns the current UTC time with timezone info."""
    return datetime.now(timezone.utc)

class BaseModel(SQLModel):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: Optional[datetime] = Field(default=None)
        
    # Method to update the timestamp automatically
    def update_timestamp(self):
        self.updated_at = utc_now()
