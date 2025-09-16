import os
import uuid
import smtplib
import base64
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session
from dotenv import load_dotenv
from typing import List

load_dotenv()

from app.db import init_db, get_session
from . import crud, models, schemas
from .utils import generate_qr_base64, build_ticket_email

# Email config from env
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER or "no-reply@example.com")

app = FastAPI(title="ticket_service")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

def send_email_smtp(msg):
    """Simple synchronous SMTP send. Kept small — executed in a background thread."""
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

def email_ticket_background(ticket_uuid: str, recipient: str, subject: str, html_body: str, qr_b64: str):
    msg = build_ticket_email(subject, recipient, html_body, qr_b64, EMAIL_FROM)
    try:
        send_email_smtp(msg)
        # Mark as emailed in DB after successful send
        # Note: open a new DB session here
        from .db import engine
        from sqlmodel import Session
        with Session(engine) as session:
            crud.mark_ticket_emailed(session, ticket_uuid)
    except Exception as exc:
        # Log error — in production use proper logging & retry/queue
        print("Failed to send ticket email:", exc)

@app.post("/tickets/issue", response_model=List[schemas.TicketRead])
def issue_tickets(req: schemas.TicketIssueRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Issue `quantity` tickets for an event after payment confirmation.
    For production you'll want to verify the payment with payment_service before issuing.
    """
    # Optional: verify payment with payment service (commented out — enable if you want)
    # import httpx
    # ps_url = os.getenv("PAYMENT_SERVICE_URL")
    # try:
    #     resp = httpx.post(f"{ps_url}/payments/verify/{req.payment_reference}", timeout=10)
    #     resp.raise_for_status()
    # except Exception:
    #     raise HTTPException(status_code=400, detail="Payment verification failed")

    created_tickets = []
    for _ in range(req.quantity):
        ticket_uuid = str(uuid.uuid4())
        # QR payload could be a signed string — here we include ticket UUID
        qr_payload = f"ticket:{ticket_uuid}|event:{req.event_id}|email:{req.user_email}"
        qr_b64 = generate_qr_base64(qr_payload)
        tcreate = schemas.TicketCreate(
            event_id=req.event_id,
            user_email=req.user_email,
            payment_reference=req.payment_reference,
            ticket_uuid=ticket_uuid,
            qr_base64=qr_b64,
            quantity=1
        )
        ticket = crud.create_ticket_record(session, tcreate)
        created_tickets.append(ticket)

        # Prepare an email HTML body; customize as needed
        html_body = f"""
        <html>
        <body>
          <h2>Your ticket for event {req.event_id}</h2>
          <p>Ticket ID: <strong>{ticket.ticket_uuid}</strong></p>
          <p>Show this QR code at the entrance:</p>
          <img src="data:image/png;base64,{qr_b64}" alt="ticket qr" />
        </body>
        </html>
        """
        # enqueue background email send
        background_tasks.add_task(email_ticket_background, ticket.ticket_uuid, req.user_email, f"Your ticket — {ticket.ticket_uuid}", html_body, qr_b64)

    return created_tickets

@app.get("/tickets/{ticket_uuid}", response_model=schemas.TicketRead)
def get_ticket(ticket_uuid: str, session: Session = Depends(get_session)):
    t = crud.get_ticket_by_uuid(session, ticket_uuid)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t

@app.get("/tickets", response_model=schemas.TicketListResponse)
def list_tickets(user_email: str = Query(...), limit: int = 100, offset: int = 0, session: Session = Depends(get_session)):
    tickets = crud.list_tickets_for_user(session, user_email, limit, offset)
    return schemas.TicketListResponse(tickets=tickets)
