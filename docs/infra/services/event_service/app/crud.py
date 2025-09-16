from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import datetime

from .models import Event
from .schemas import EventCreate, EventUpdate

# Create
def create_event(session: Session, event_in: EventCreate) -> Event:
    """
    Create and persist a new Event.
    """
    event = Event(
        title=event_in.title,
        description=event_in.description,
        date=event_in.date,
        location=event_in.location,
        category=event_in.category,
        price=event_in.price,
        total_tickets=event_in.total_tickets,
        available_tickets=event_in.total_tickets
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

# Read - by id
def get_event_by_id(session: Session, event_id: int) -> Optional[Event]:
    """
    Return Event by primary key or None if not found.
    """
    return session.get(Event, event_id)

# Read - list with filters
def list_events(
    session: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Event]:
    """
    Return a list of events filtered by optional parameters.
    - start_date / end_date: datetime objects (inclusive)
    - category: exact match
    - q: substring search on title OR description
    """
    statement = select(Event)

    if start_date:
        statement = statement.where(Event.date >= start_date)
    if end_date:
        statement = statement.where(Event.date <= end_date)
    if category:
        statement = statement.where(Event.category == category)
    if q:
        # NOTE: contains() translates to LIKE for most SQL backends
        statement = statement.where((Event.title.contains(q)) | (Event.description.contains(q)))

    statement = statement.limit(limit).offset(offset)
    results = session.exec(statement).all()
    return results

# Update
def update_event(session: Session, event_id: int, event_in: EventUpdate) -> Optional[Event]:
    """
    Apply partial updates from EventUpdate to an existing Event.
    Returns the updated Event or None if not found.
    """
    event = session.get(Event, event_id)
    if not event:
        return None

    update_data: Dict[str, Any] = event_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    # Ensure available_tickets doesn't exceed total_tickets
    if getattr(event, "available_tickets", None) is not None and getattr(event, "total_tickets", None) is not None:
        if event.available_tickets > event.total_tickets:
            event.available_tickets = event.total_tickets

    session.add(event)
    session.commit()
    session.refresh(event)
    return event

# Delete
def delete_event(session: Session, event_id: int) -> bool:
    """
    Delete an event. Returns True if deleted, False if not found.
    """
    event = session.get(Event, event_id)
    if not event:
        return False
    session.delete(event)
    session.commit()
    return True

# Utility: try-reserve tickets (atomic-ish)
def try_reserve_tickets(session: Session, event_id: int, quantity: int) -> bool:
    """
    Try to reserve `quantity` tickets by decrementing available_tickets.
    Returns True if reservation succeeded, False if not enough tickets or not found.
    Note: this is a simple implementation and may need DB-level locking for concurrency in production.
    """
    event = session.get(Event, event_id)
    if not event:
        return False
    if event.available_tickets is None or event.available_tickets < quantity:
        return False
    event.available_tickets -= quantity
    session.add(event)
    session.commit()
    session.refresh(event)
    return True
