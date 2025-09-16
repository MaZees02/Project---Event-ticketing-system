# import os
# import json
# import time
# from typing import Optional
# from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
# from fastapi.security import OAuth2PasswordBearer
# from sqlmodel import Session
# import httpx
# from dotenv import load_dotenv

# from app.db import init_db, get_session
# from app import crud, schemas

# load_dotenv()

# # Config
# PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
# PAYSTACK_BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
# CALLBACK_URL = os.getenv("PAYMENT_CALLBACK_URL", "http://localhost:8003/payments/verify")  # ticket_service or frontend callback
# CURRENCY = os.getenv("CURRENCY", "NGN")

# # Simple OAuth2 token dependency placeholder (decodes JWT to get the sub claim)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl=os.getenv("USER_TOKEN_URL", "http://localhost:8001/auth/token"))

# def decode_jwt_get_email(token: str = Depends(oauth2_scheme)) -> str:
#     # For simplicity, decode the token to read 'sub' claim.
#     # You can replace with a proper decode + signature verification as in other services.
#     from jose import jwt, JWTError
#     SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
#     ALGORITHM = os.getenv("ALGORITHM", "HS256")
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: Optional[str] = payload.get("sub")
#         if email is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token (no subject)")
#         return email
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

# # --- Simple in-process circuit breaker ---
# class CircuitBreaker:
#     CLOSED = "closed"
#     OPEN = "open"
#     HALF_OPEN = "half_open"

#     def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
#         self.failure_threshold = failure_threshold
#         self.recovery_timeout = recovery_timeout  # seconds
#         self.fail_count = 0
#         self.state = CircuitBreaker.CLOSED
#         self.opened_since = None

#     def _enter_open(self):
#         self.state = CircuitBreaker.OPEN
#         self.opened_since = time.time()

#     def _enter_half_open(self):
#         self.state = CircuitBreaker.HALF_OPEN

#     def _enter_closed(self):
#         self.state = CircuitBreaker.CLOSED
#         self.fail_count = 0
#         self.opened_since = None

#     def record_success(self):
#         # on success reset
#         self._enter_closed()

#     def record_failure(self):
#         self.fail_count += 1
#         if self.fail_count >= self.failure_threshold:
#             self._enter_open()

#     def allow_request(self) -> bool:
#         if self.state == CircuitBreaker.CLOSED:
#             return True
#         if self.state == CircuitBreaker.OPEN:
#             # check timeout
#             if (time.time() - (self.opened_since or 0)) > self.recovery_timeout:
#                 self._enter_half_open()
#                 return True
#             return False
#         if self.state == CircuitBreaker.HALF_OPEN:
#             # allow one request to probe
#             return True
#         return False

# # Create a circuit breaker instance for Paystack calls
# paystack_cb = CircuitBreaker(failure_threshold=int(os.getenv("CB_FAILURE_THRESHOLD", "3")), recovery_timeout=int(os.getenv("CB_RECOVERY_TIMEOUT", "30")))

# # Helper: call Paystack initialize
# def call_paystack_initialize(email: str, amount: int, reference: Optional[str] = None):
#     """
#     amount: integer in kobo if NGN (Paystack expects smallest currency unit).
#     returns the json response from Paystack.
#     """
#     if not paystack_cb.allow_request():
#         raise HTTPException(status_code=503, detail="Payment gateway temporarily unavailable (circuit open)")

#     url = f"{PAYSTACK_BASE_URL}/transaction/initialize"
#     payload = {
#         "email": email,
#         "amount": amount,
#         "callback_url": CALLBACK_URL,
#     }
#     if reference:
#         payload["reference"] = reference

#     headers = {
#         "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
#         "Content-Type": "application/json"
#     }

#     try:
#         with httpx.Client(timeout=15.0) as client:
#             resp = client.post(url, json=payload, headers=headers)
#             resp.raise_for_status()
#             data = resp.json()
#             # success -> reset circuit breaker
#             paystack_cb.record_success()
#             return data
#     except Exception as exc:
#         # record failure and possibly open circuit
#         paystack_cb.record_failure()
#         raise HTTPException(status_code=502, detail=f"Payment gateway error: {str(exc)}")

# # Helper: verify transaction
# def call_paystack_verify(reference: str):
#     if not paystack_cb.allow_request():
#         raise HTTPException(status_code=503, detail="Payment gateway temporarily unavailable (circuit open)")
#     url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"
#     headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
#     try:
#         with httpx.Client(timeout=15.0) as client:
#             resp = client.get(url, headers=headers)
#             resp.raise_for_status()
#             data = resp.json()
#             paystack_cb.record_success()
#             return data
#     except Exception as exc:
#         paystack_cb.record_failure()
#         raise HTTPException(status_code=502, detail=f"Payment gateway error: {str(exc)}")


# app = FastAPI(title="payment_service", version="0.1")

# @app.on_event("startup")
# def on_startup():
#     init_db()

# @app.get("/health", tags=["health"])
# def health():
#     return {"status": "ok"}

# # Endpoint: initiate payment. Protected.
# @app.post("/payments/initiate", response_model=schemas.PaymentInitResponse, tags=["payments"])
# def initiate_payment(payment_in: schemas.PaymentCreate, user_email: str = Depends(decode_jwt_get_email), session: Session = Depends(get_session)):
#     # Validate user_email matches token (or override)
#     if payment_in.user_email != user_email:
#         # optional: allow admins to initialize for others
#         raise HTTPException(status_code=403, detail="Authenticated user does not match payment owner")

#     # Create internal payment record with placeholder reference (we'll use Paystack's reference returned)
#     # Convert amount to smallest currency unit (Paystack expects e.g. kobo). We'll assume NGN and multiply by 100.
#     amt_smallest_unit = int(payment_in.amount * 100)

#     # Call Paystack initialize via circuit breaker
#     paystack_resp = call_paystack_initialize(payment_in.user_email, amt_smallest_unit)
#     # Expected structure: { "status": True, "message": "...", "data": { "authorization_url": "...", "access_code": "...", "reference": "..." } }

#     data = paystack_resp.get("data", {}) if isinstance(paystack_resp, dict) else {}
#     reference = data.get("reference")
#     authorization_url = data.get("authorization_url")
#     access_code = data.get("access_code")

#     # Persist payment record using reference from Paystack (if present)
#     payment = crud.create_payment(session=session, payment_in=payment_in, reference=reference)
#     # Optionally store raw paystack response
#     crud.update_payment_status(session=session, reference=reference, status="pending", paystack_response=json.dumps(paystack_resp))

#     return schemas.PaymentInitResponse(
#         authorization_url=authorization_url,
#         access_code=access_code,
#         reference=reference
#     )

# # Endpoint: verify payment (can be used by frontend callback or called manually)
# @app.get("/payments/verify/{reference}", response_model=schemas.PaystackVerifyResponse, tags=["payments"])
# def verify_payment(reference: str, session: Session = Depends(get_session)):
#     paystack_resp = call_paystack_verify(reference)
#     # Inspect response to determine success
#     status_bool = paystack_resp.get("status", False)
#     data = paystack_resp.get("data", {})
#     message = paystack_resp.get("message")
#     if status_bool and data.get("status") == "success":
#         # mark payment as paid
#         crud.update_payment_status(session=session, reference=reference, status="paid", paystack_response=json.dumps(paystack_resp))
#         # TODO: notify ticket_service to issue ticket(s) (call ticket_service / message queue)
#     else:
#         # mark as failed
#         crud.update_payment_status(session=session, reference=reference, status="failed", paystack_response=json.dumps(paystack_resp))

#     return schemas.PaystackVerifyResponse(status=status_bool, message=message, data=data)

# # Endpoint: Paystack webhook receiver (POST). Configure webhook on Paystack dashboard to hit this.
# @app.post("/payments/webhook", status_code=200, tags=["payments"])
# async def paystack_webhook(request: Request, session: Session = Depends(get_session)):
#     """
#     Receives Paystack webhook events.
#     Validate Paystack signature in production.
#     """
#     payload = await request.body()
#     try:
#         data = await request.json()
#     except Exception:
#         data = None

#     # Example: you may validate the signature header using PAYSTACK_SECRET_KEY
#     # Process event: update payment if reference present
#     event = data.get("event") if isinstance(data, dict) else None
#     event_data = data.get("data") if isinstance(data, dict) else None
#     ref = None
#     if event_data:
#         ref = event_data.get("reference") or event_data.get("reference_id") or event_data.get("id")
#     if ref:
#         # call verify to be safe
#         try:
#             call_paystack_verify(ref)
#         except HTTPException:
#             # ignore for webhook (will retry)
#             pass

#     # respond with 200 to acknowledge
#     return {"received": True, "event": event}

# # Admin: get payment by reference (protected)
# @app.get("/payments/{reference}", response_model=schemas.PaymentRead, tags=["payments"])
# def get_payment(reference: str, user_email: str = Depends(decode_jwt_get_email), session: Session = Depends(get_session)):
#     payment = crud.get_payment_by_reference(session, reference)
#     if not payment:
#         raise HTTPException(status_code=404, detail="Payment not found")
#     # ensure user owns the payment (unless admin)
#     if payment.user_email != user_email:
#         raise HTTPException(status_code=403, detail="Forbidden")
#     return payment

import os
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sqlmodel import Session
import uuid
import hmac
import hashlib

load_dotenv()

from app.db import init_db, get_session
from .schemas import PaymentInitiateRequest, PaymentInitiateResponse, PaymentRecord, VerifyResponse
from . import crud
from .paystack_client import initialize_transaction, verify_transaction, circuit

app = FastAPI(title="payment_service")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
async def health():
    return {"status": "ok", "circuit_state": circuit.state.value}

@app.post("/payments/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(req: PaymentInitiateRequest, session: Session = Depends(get_session)):
    """
    Initiate a Paystack transaction and store a payment record.
    Amount must be in smallest currency unit (kobo for NGN).
    """
    # Generate our own reference if caller didn't include it
    reference = str(uuid.uuid4())

    # Check circuit
    if not circuit.allow_request():
        raise HTTPException(status_code=503, detail="Payment gateway temporarily unavailable (circuit open)")

    try:
        data = await initialize_transaction(req.email, req.amount, req.callback_url, req.metadata)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        # If Paystack call failed, surface error
        raise HTTPException(status_code=502, detail="Failed to contact payment gateway") from exc

    # Paystack returns access_code and authorization_url in data['data']
    paystack_data = data.get("data") or {}
    access_code = paystack_data.get("access_code")
    authorization_url = paystack_data.get("authorization_url") or paystack_data.get("auth_url") or ""

    # Save record (use Paystack reference if provided; fallback to our generated one)
    ps_reference = paystack_data.get("reference") or reference
    payment = crud.create_payment_record(session, ps_reference, req, status="initialized")

    return PaymentInitiateResponse(
        reference=ps_reference,
        authorization_url=authorization_url,
        access_code=access_code,
        status=data.get("status", "unknown")
    )

@app.get("/payments/{reference}", response_model=PaymentRecord)
async def get_payment(reference: str, session: Session = Depends(get_session)):
    p = crud.get_payment_by_reference(session, reference)
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    return p

# Endpoint to actively verify a transaction with Paystack (sync to webhook)
@app.post("/payments/verify/{reference}", response_model=VerifyResponse)
async def verify(reference: str, session: Session = Depends(get_session)):
    try:
        data = await verify_transaction(reference)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to verify with payment gateway") from exc

    # Paystack verify payload usually contains 'data' with 'status' and 'amount'
    psdata = data.get("data") or {}
    status = psdata.get("status")
    # Map status to our record
    if status == "success":
        crud.update_payment_status(session, reference, "success", data=psdata)
    else:
        crud.update_payment_status(session, reference, "failed", data=psdata)

    return VerifyResponse(status=True, message="Verification complete", data=psdata)

# Webhook endpoint Paystack will POST to after payment
@app.post("/payments/webhook")
async def webhook(request: Request, x_paystack_signature: str | None = Header(None), session: Session = Depends(get_session)):
    raw_body = await request.body()
    # Optional: verify signature if PAYSTACK_SECRET_KEY is present
    secret = os.getenv("PAYSTACK_SECRET_KEY", "")
    if x_paystack_signature and secret:
        computed = hmac.new(secret.encode(), raw_body, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(computed, x_paystack_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    # Paystack sends event and data
    event = payload.get("event")
    data = payload.get("data") or {}
    reference = data.get("reference")
    status = data.get("status")

    if reference:
        if status == "success":
            crud.update_payment_status(session, reference, "success", data=data)
            # TODO: trigger ticket issuance (call ticket_service) or send async message to queue
        else:
            crud.update_payment_status(session, reference, "failed", data=data)

    return JSONResponse({"received": True})

# Admin: list circuit state / stats
@app.get("/circuit")
async def circuit_state():
    return {
        "state": circuit.state.value,
        "failures": circuit.failures,
        "max_failures": circuit.max_failures,
        "reset_timeout": circuit.reset_timeout
    }
