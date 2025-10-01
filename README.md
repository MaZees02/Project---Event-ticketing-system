<<<<<<< HEAD

=======
🎟️ Event Ticketing System

A modular event ticketing platform built with FastAPI.
It allows users to register, browse events, purchase tickets via Paystack, and receive QR-code-based tickets via email.

📌 Features

User Service – User registration, authentication (JWT), and profile management.

Event Service – CRUD for events, public listing & filtering.

Payment Service – Integration with Paystack (with circuit breaker fallback).

Ticket Service – Ticket issuance, QR code generation, email delivery.

Dockerized for easy deployment.

🏗️ Architecture

event_ticketing/
│── services/
│   ├── user_service/
│   ├── event_service/
│   ├── payment_service/
│   ├── ticket_service/
│── infra/                # Docker, reverse proxy configs
│── docs/                 # API documentation
│── docker-compose.yml
│── README.md
│── .gitignore

Each service has its own:

main.py (FastAPI app entrypoint)
models.py, schemas.py, crud.py, db.py
requirements.txt
.env file (for secrets and configs)

Services will be available at:

User Service → http://localhost:8001/docs

Event Service → http://localhost:8002/docs

Payment Service → http://localhost:8003/docs

Ticket Service → http://localhost:8004/docs

>>>>>>> c016af0 (Add requirements.txt for Render deployment)
