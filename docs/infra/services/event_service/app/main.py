# # inside app/main.py (pseudo)
# from . import crud
# from .db import get_session
# from .db import init_db

# @app.on_event("startup")
# def on_startup():
#     init_db()


# @app.post("/events", response_model=EventRead)
# def create_event_endpoint(event_in: EventCreate, session: Session = Depends(get_session), user_email: str = Depends(get_current_user_email)):
#     event = crud.create_event(session, event_in)
#     return event

# @app.get("/events/{event_id}", response_model=EventRead)
# def get_event_endpoint(event_id: int, session: Session = Depends(get_session)):
#     event = crud.get_event_by_id(session, event_id)
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found")
#     return event

# @app.get("/events", response_model=list[EventRead])
# def list_events_endpoint(start_date: Optional[str] = None, session: Session = Depends(get_session)):
#     # parse start_date/end_date to datetime if provided...
#     events = crud.list_events(session, start_dt, end_dt, category, q, limit, offset)
#     return events

# @app.put("/events/{event_id}", response_model=EventRead)
# def update_event_endpoint(event_id: int, event_update: EventUpdate, session: Session = Depends(get_session), user_email: str = Depends(get_current_user_email)):
#     updated = crud.update_event(session, event_id, event_update)
#     if not updated:
#         raise HTTPException(status_code=404, detail="Event not found")
#     return updated

# @app.delete("/events/{event_id}")
# def delete_event_endpoint(event_id: int, session: Session = Depends(get_session), user_email: str = Depends(get_current_user_email)):
#     ok = crud.delete_event(session, event_id)
#     if not ok:
#         raise HTTPException(status_code=404, detail="Event not found")
#     return Response(status_code=204)


from fastapi import FastAPI, Depends, HTTPException, Response
from typing import Optional
from sqlmodel import Session

from app import crud, schemas
from .db import get_session, init_db

app = FastAPI(title="Event Service")

# Startup hook to create tables
@app.on_event("startup")
def on_startup():
    init_db()

# ----- Endpoints -----

@app.post("/events", response_model=schemas.EventRead)
def create_event_endpoint(
    event_in: schemas.EventCreate,
    session: Session = Depends(get_session)
):
    event = crud.create_event(session, event_in)
    return event


@app.get("/events/{event_id}", response_model=schemas.EventRead)
def get_event_endpoint(event_id: int, session: Session = Depends(get_session)):
    event = crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.get("/events", response_model=list[schemas.EventRead])
def list_events_endpoint(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session)
):
    events = crud.list_events(session, start_date, end_date, category, q, limit, offset)
    return events


@app.put("/events/{event_id}", response_model=schemas.EventRead)
def update_event_endpoint(
    event_id: int,
    event_update: schemas.EventUpdate,
    session: Session = Depends(get_session)
):
    updated = crud.update_event(session, event_id, event_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated


@app.delete("/events/{event_id}")
def delete_event_endpoint(event_id: int, session: Session = Depends(get_session)):
    ok = crud.delete_event(session, event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Event not found")
    return Response(status_code=204)
