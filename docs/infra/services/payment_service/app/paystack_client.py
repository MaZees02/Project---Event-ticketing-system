import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.circuit_breaker import CircuitBreaker

PAYSTACK_BASE = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
PAYSTACK_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
MAX_FAILURES = int(os.getenv("CIRCUIT_MAX_FAILURES", "3"))
RESET_SECONDS = int(os.getenv("CIRCUIT_RESET_SECONDS", "60"))

circuit = CircuitBreaker(max_failures=MAX_FAILURES, reset_timeout=RESET_SECONDS)

HEADERS = {
    "Authorization": f"Bearer {PAYSTACK_KEY}",
    "Content-Type": "application/json"
}

async def initialize_transaction(email: str, amount: int, callback_url: str | None = None, metadata: dict | None = None):
    if not circuit.allow_request():
        raise RuntimeError("Paystack circuit is open — rejecting request")

    payload = {"email": email, "amount": amount}
    if callback_url:
        payload["callback_url"] = callback_url
    if MetaData:
        payload["metadata"] = MetaData

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(f"{PAYSTACK_BASE}/transaction/initialize", json=payload, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
            # success -> reset circuit
            circuit.record_success()
            return data
        except Exception as exc:
            # record failure and rethrow
            circuit.record_failure()
            raise

async def verify_transaction(reference: str):
    if not circuit.allow_request():
        raise RuntimeError("Paystack circuit is open — rejecting request")
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(f"{PAYSTACK_BASE}/transaction/verify/{reference}", headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
            circuit.record_success()
            return data
        except Exception:
            circuit.record_failure()
            raise
