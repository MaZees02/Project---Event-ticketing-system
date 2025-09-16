# from sqlmodel import Session, select
# from typing import Optional
# from datetime import datetime
# from app.models import Payment
# from .schemas import PaymentCreate
# #from .schemas import PaymentCreateSchema

# def create_payment(session: Session, payment_in: PaymentCreate, reference: str | None = None) -> Payment:
#     payment = Payment(
#         user_email=payment_in.user_email,
#         event_id=payment_in.event_id,
#         quantity=payment_in.quantity,
#         amount=payment_in.amount,
#         reference=reference,
#         status="pending"
#     )
#     session.add(payment)
#     session.commit()
#     session.refresh(payment)
#     return payment

# def get_payment_by_id(session: Session, payment_id: int) -> Optional[Payment]:
#     return session.get(Payment, payment_id)

# def get_payment_by_reference(session: Session, reference: str) -> Optional[Payment]:
#     statement = select(Payment).where(Payment.reference == reference)
#     return session.exec(statement).first()

# def update_payment_status(session: Session, reference: str, status: str, paystack_response: Optional[str] = None) -> Optional[Payment]:
#     payment = get_payment_by_reference(session, reference)
#     if not payment:
#         return None
#     payment.status = status
#     payment.paystack_response = paystack_response or payment.paystack_response
#     payment.updated_at = datetime.utcnow()
#     session.add(payment)
#     session.commit()
#     session.refresh(payment)
#     return payment

from sqlmodel import Session, select
from app.models import Payment
from .schemas import PaymentInitiateRequest
from datetime import datetime
import json

def create_payment_record(session: Session, reference: str, req: PaymentInitiateRequest, status: str = "initialized") -> Payment:
    payment = Payment(
        event_id=req.event_id,
        user_email=req.email,
        reference=reference,
        amount=req.amount,
        currency=req.currency or "NGN",
        status=status,
        metadata=json.dumps(req.metadata) if req.metadata else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment

def get_payment_by_reference(session: Session, reference: str):
    statement = select(Payment).where(Payment.reference == reference)
    return session.exec(statement).first()

def update_payment_status(session: Session, reference: str, status: str, data: dict | None = None):
    payment = get_payment_by_reference(session, reference)
    if not payment:
        return None
    payment.status = status
    payment.updated_at = datetime.utcnow()
    # Optionally store verification payload in metadata
    if data is not None:
        import json
        existing = {}
        if payment.MetaData:
            try:
                existing = json.loads(payment.MetaData)
            except Exception:
                existing = {}
        existing["_verify"] = data
        payment.metadata = json.dumps(existing)
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment
