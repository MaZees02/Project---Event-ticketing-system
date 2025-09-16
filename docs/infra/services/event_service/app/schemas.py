from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# ----- Shared -----
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    total_tickets: int
    available_tickets: Optional[int] = None

# ----- Create -----
class EventCreate(EventBase):
    pass

# ----- Update -----
class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_tickets: Optional[int] = None
    available_tickets: Optional[int] = None

# ----- Read (response model) -----
class EventRead(EventBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
