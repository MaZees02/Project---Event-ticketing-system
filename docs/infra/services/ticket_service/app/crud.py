from sqlmodel import Session, select
from app.models import Ticket
from .schemas import TicketCreate
from datetime import datetime
from typing import List, Optional

def create_ticket_record(session: Session, ticket_in: TicketCreate) -> Ticket:
    t = Ticket(
        ticket_uuid=ticket_in.ticket_uuid,
        event_id=ticket_in.event_id,
        user_email=str(ticket_in.user_email),
        payment_reference=ticket_in.payment_reference,
        qr_base64=ticket_in.qr_base64,
        quantity=ticket_in.quantity,
        status="issued",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(t)
    session.commit()
    session.refresh(t)
    return t

def get_ticket_by_uuid(session: Session, ticket_uuid: str) -> Optional[Ticket]:
    statement = select(Ticket).where(Ticket.ticket_uuid == ticket_uuid)
    return session.exec(statement).first()

def list_tickets_for_user(session: Session, user_email: str, limit: int = 100, offset: int = 0) -> List[Ticket]:
    statement = select(Ticket).where(Ticket.user_email == user_email).limit(limit).offset(offset)
    return session.exec(statement).all()

def mark_ticket_emailed(session: Session, ticket_uuid: str) -> Optional[Ticket]:
    t = get_ticket_by_uuid(session, ticket_uuid)
    if not t:
        return None
    t.status = "emailed"
    t.updated_at = datetime.utcnow()
    session.add(t)
    session.commit()
    session.refresh(t)
    return t
