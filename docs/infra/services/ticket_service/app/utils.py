import qrcode
import io
import base64
from email.message import EmailMessage
from email.utils import formataddr
import os

def generate_qr_base64(payload: str) -> str:
    """
    Generate QR code PNG as base64 string.
    Payload is usually a ticket UUID or signed payload.
    """
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return b64

def build_ticket_email(subject: str, to_email: str, html_body: str, qr_base64: str, email_from: str):
    """
    Return an EmailMessage with PNG attachment built from base64.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Event Tickets", email_from))
    msg["To"] = to_email
    msg.set_content("Your ticket is attached. If you don't see the image, view HTML version.")
    msg.add_alternative(html_body, subtype="html")
    # Attach PNG
    png_data = base64.b64decode(qr_base64)
    msg.add_attachment(png_data, maintype="image", subtype="png", filename="ticket_qr.png")
    return msg
