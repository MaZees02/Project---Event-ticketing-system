from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class TicketIssueRequest(BaseModel):
    event_id: int
    user_email: EmailStr
    payment_reference: str
    quantity: int = 1  # number of tickets to issue

class TicketCreate(BaseModel):
    event_id: int
    user_email: EmailStr
    payment_reference: str
    ticket_uuid: str
    qr_base64: Optional[str] = None
    quantity: int = 1

class TicketRead(BaseModel):
    id: int
    ticket_uuid: str
    event_id: Optional[int] = None
    user_email: Optional[EmailStr] = None
    payment_reference: Optional[str] = None
    quantity: int
    status: str
    qr_base64: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class TicketListResponse(BaseModel):
    tickets: List[TicketRead]
