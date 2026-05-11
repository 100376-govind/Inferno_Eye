# backend/services/otp_service.py
"""
OTP generation, storage (in-memory with TTL), and email dispatch.
SMTP credentials come from environment variables. If not set, OTP is
printed to the console so development still works without email setup.
"""
import os
import time
import random
import string
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
SMTP_HOST  = os.getenv("SMTP_HOST",  "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT",  "587"))
SMTP_USER  = os.getenv("SMTP_USER",  "")   # your-email@gmail.com
SMTP_PASS  = os.getenv("SMTP_PASS",  "")   # app password
FROM_NAME  = os.getenv("SMTP_FROM_NAME", "Inferno Eye")
OTP_TTL    = int(os.getenv("OTP_TTL_SECONDS", "600"))   # 10 min
OTP_LENGTH = 6

# ── In-memory OTP store: username -> (otp, expiry_timestamp) ────────────────
_store: Dict[str, Tuple[str, float]] = {}


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


def create_and_store_otp(username: str) -> str:
    otp = _generate_otp()
    _store[username] = (otp, time.time() + OTP_TTL)
    logger.info(f"OTP generated for {username} (expires in {OTP_TTL}s)")
    return otp


def verify_otp(username: str, otp: str) -> bool:
    record = _store.get(username)
    if not record:
        return False
    stored_otp, expiry = record
    if time.time() > expiry:
        _store.pop(username, None)
        return False
    if stored_otp != otp.strip():
        return False
    _store.pop(username, None)   # single-use
    return True


def send_otp_email(to_email: str, username: str, otp: str) -> None:
    """Send OTP via SMTP. Falls back to console log when SMTP not configured."""
    if not SMTP_USER or not SMTP_PASS:
        # Dev fallback — print to stdout so the developer can see the OTP
        print(f"\n{'='*50}")
        print(f"  🔥 INFERNO EYE — OTP for {username}: {otp}")
        print(f"  (SMTP not configured — check console)")
        print(f"{'='*50}\n")
        logger.warning("SMTP not configured. OTP printed to console.")
        return

    html = f"""
    <html><body style="background:#0a0d12;color:#e5e7eb;font-family:Inter,sans-serif;padding:32px">
      <div style="max-width:480px;margin:0 auto;background:#0f1319;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:32px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px">
          <span style="font-size:28px">🔥</span>
          <span style="font-size:20px;font-weight:800;color:#f97316;letter-spacing:0.1em">INFERNO EYE</span>
        </div>
        <h2 style="font-size:18px;font-weight:700;margin-bottom:8px">Your Verification Code</h2>
        <p style="color:#9ca3af;font-size:14px;margin-bottom:24px">
          Hello <strong style="color:#e5e7eb">{username}</strong>,<br>
          Use the code below to complete your sign-in. It expires in <strong>10 minutes</strong>.
        </p>
        <div style="background:#1c2433;border:1px solid rgba(249,115,22,0.3);border-radius:10px;padding:24px;text-align:center;margin-bottom:24px">
          <span style="font-size:40px;font-weight:800;letter-spacing:0.3em;color:#f97316;font-family:monospace">{otp}</span>
        </div>
        <p style="color:#6b7280;font-size:12px;line-height:1.6">
          If you didn't request this code, please ignore this email.<br>
          This code is valid for <strong>10 minutes</strong> and can only be used once.
        </p>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:20px 0">
        <p style="color:#4b5563;font-size:11px;text-align:center">
          Inferno Eye · AI Fire Detection Command Center · Kolkata, West Bengal
        </p>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔥 Inferno Eye — Your OTP: {otp}"
    msg["From"]    = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        logger.info(f"OTP email sent to {to_email}")
    except Exception as exc:
        logger.error(f"SMTP send failed: {exc}. OTP for {username}: {otp}")
        # Still print to console as fallback
        print(f"\n🔥 OTP for {username}: {otp}  (email send failed)\n")
