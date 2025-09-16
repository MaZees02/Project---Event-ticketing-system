# from typing import Optional
# from datetime import datetime
# from sqlmodel import SQLModel, Field

# class Payment(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     user_email: Optional[str] = Field(index=True, default=None)
#     event_id: Optional[int] = None
#     quantity: int = 1
#     amount: float = 0.0  # amount in the currency unit (e.g., NGN)
#     reference: Optional[str] = Field(index=True, default=None, nullable=True, unique=True)
#     status: str = Field(default="pending")  # pending | paid | failed | cancelled
#     paystack_response: Optional[str] = None  # store raw JSON string if needed
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: datetime = Field(default_factory=datetime.utcnow)

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: Optional[int] = None         # link to event (optional)
    user_email: Optional[str] = None       # payer identifier
    reference: str = Field(index=True, nullable=False, unique=True)
    amount: int = 0                        # amount in kobo / smallest currency unit
    currency: str = "NGN"
    status: str = "initialized"            # initialized, success, failed, pending
    channel: Optional[str] = None
    MetaData: Optional[str] = None        # JSON string if needed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
