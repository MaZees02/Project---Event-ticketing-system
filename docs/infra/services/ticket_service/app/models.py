from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Ticket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_uuid: str = Field(index=True, nullable=False, unique=True)  # public ticket id (UUID)
    event_id: Optional[int] = None
    user_email: Optional[str] = None
    payment_reference: Optional[str] = None
    quantity: int = 1
    qr_base64: Optional[str] = None  # base64-encoded PNG image
    status: str = Field(default="issued")  # issued, emailed, used, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
