# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from datetime import datetime

# class PaymentCreate(BaseModel):
#     user_email: EmailStr
#     event_id: int
#     quantity: int = 1
#     amount: float  # must match event price * quantity on caller side

# class PaymentRead(BaseModel):
#     id: int
#     user_email: EmailStr
#     event_id: int
#     quantity: int
#     amount: float
#     reference: Optional[str]
#     status: str
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         orm_mode = True

# class PaymentInitResponse(BaseModel):
#     authorization_url: str
#     access_code: Optional[str] = None
#     reference: Optional[str] = None

# class PaystackVerifyResponse(BaseModel):
#     status: bool
#     message: Optional[str] = None
#     data: Optional[dict] = None

from pydantic import BaseModel, EmailStr
from typing import Optional, Any

class PaymentInitiateRequest(BaseModel):
    email: EmailStr
    amount: int              # amount in kobo (e.g., ₦100 => 10000)
    event_id: Optional[int] = None
    MetaData: Optional[dict] = None
    currency: Optional[str] = "NGN"
    callback_url: Optional[str] = None

class PaymentInitiateResponse(BaseModel):
    reference: str
    authorization_url: str
    access_code: Optional[str] = None
    status: str

class PaymentRecord(BaseModel):
    id: int
    reference: str
    amount: int
    currency: str
    status: str
    user_email: Optional[EmailStr] = None
    event_id: Optional[int] = None

    class Config:
        orm_mode = True

class VerifyResponse(BaseModel):
    status: bool
    message: Optional[str] = None
    data: Optional[Any] = None
