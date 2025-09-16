from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    total_tickets: int = Field(default=0)
    available_tickets: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
