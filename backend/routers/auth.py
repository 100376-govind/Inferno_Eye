# backend/routers/auth.py
"""
Admin authentication — register, login, OTP verification.
Uses PBKDF2 for password hashing and returns a simple HS256 JWT.
OTP emails are sent via SMTP (Gmail). If SMTP_EMAIL is not configured,
the OTP is printed to the console as a dev fallback.
"""
import os
import time
import hashlib
import hmac
import base64
import json
import random
import string
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import AdminUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

# ── Stores ──────────────────────────────────────────────────────────────────
# OTP store: { username: (otp_code, expiry_timestamp) }
_otp_store: Dict[str, Tuple[str, float]] = {}

# Pending registrations: { username: { name, email, password_hash, expiry } }
_pending_registrations: Dict[str, dict] = {}

OTP_TTL = 600  # 10 minutes


SECRET_KEY = os.getenv("JWT_SECRET", "inferno-eye-super-secret-2024-change-me")
TOKEN_TTL  = 60 * 60 * 24  # 24 hours


# ── Pydantic schemas ────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def username_min(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_min(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


class LoginRequest(BaseModel):
    username: str
    password: str


class SendOTPRequest(BaseModel):
    username: str
    password: str


class VerifyOTPRequest(BaseModel):
    username: str
    otp: str


class TokenResponse(BaseModel):
    token: str
    username: str
    name: str
    email: str
    role: str


class OTPSentResponse(BaseModel):
    message: str
    masked_email: str


# ── Helpers ─────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """SHA-256 PBKDF2 — no external deps needed."""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, dk_hex = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _make_token(user: "AdminUser") -> str:
    """Build a simple HS256-like JWT (header.payload.sig)."""
    header  = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({
        "sub":      str(user.id),
        "username": user.username,
        "email":    user.email,
        "role":     user.role,
        "iat":      int(time.time()),
        "exp":      int(time.time()) + TOKEN_TTL,
    }).encode()).decode().rstrip("=")
    sig_bytes = hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(sig_bytes).decode().rstrip("=")
    return f"{header}.{payload}.{sig}"


# ── OTP helpers ──────────────────────────────────────────────────────────────

def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def _mask_email(email: str) -> str:
    parts = email.split("@")
    if len(parts) != 2:
        return email
    local = parts[0]
    masked = local[0] + "*" * (len(local) - 2) + local[-1] if len(local) > 2 else local[0] + "*"
    return f"{masked}@{parts[1]}"


def _send_otp_email(to_email: str, username: str, otp: str) -> None:
    """Send OTP via Gmail SMTP. Falls back to console log if not configured."""
    smtp_email = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASS", "")

    if not smtp_email or not smtp_password:
        # Dev fallback — print to console
        logger.info(f"[DEV OTP] Username: {username} | OTP: {otp} | To: {to_email}")
        print(f"\n{'='*50}\n🔑  OTP for {username}: {otp}  (expires in 10 min)\n{'='*50}\n")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🔥 Inferno Eye — Your Sign-In OTP"
    msg["From"] = f"Inferno Eye <{smtp_email}>"
    msg["To"] = to_email

    html = f"""
    <html><body style="margin:0;padding:0;background:#0a0d12;font-family:Inter,sans-serif">
      <div style="max-width:480px;margin:40px auto;background:#0f1319;border:1px solid rgba(249,115,22,0.3);
                  border-radius:16px;overflow:hidden">
        <div style="background:linear-gradient(135deg,#f97316,#ef4444);padding:24px;text-align:center">
          <h1 style="color:#fff;margin:0;font-size:22px;letter-spacing:2px">🔥 INFERNO EYE</h1>
          <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px">AI Fire Detection Command Center</p>
        </div>
        <div style="padding:32px;text-align:center">
          <p style="color:#9ca3af;margin:0 0 20px">Hi <b style="color:#e5e7eb">{username}</b>, your sign-in OTP is:</p>
          <div style="background:#1c2433;border:1px solid rgba(249,115,22,0.4);border-radius:12px;
                      padding:20px;letter-spacing:12px;font-size:36px;font-weight:800;color:#f97316">
            {otp}
          </div>
          <p style="color:#6b7280;margin:20px 0 0;font-size:12px">This code expires in <b style="color:#9ca3af">10 minutes</b>.<br>
          If you did not request this, please ignore this email.</p>
        </div>
        <div style="padding:16px;text-align:center;border-top:1px solid rgba(255,255,255,0.07)">
          <p style="color:#4b5563;font-size:11px;margin:0">Inferno Eye · AI + IoT + Blockchain · Kolkata, West Bengal</p>
        </div>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        # 10-second timeout to prevent API hanging
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        logger.info(f"OTP email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        # Detailed warning to terminal
        print(f"\n{'!'*50}\n❌  ERROR: Could not send OTP email to {to_email}")
        print(f"    Reason: {e}")
        print(f"    FALLBACK: OTP for {username} is {otp}")
        print(f"{'!'*50}\n")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=OTPSentResponse)
async def register(body: RegisterRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Validate data, generate OTP, store in-memory, send email. User NOT created in DB yet."""
    # Check username taken in DB
    existing = await db.execute(select(AdminUser).where(AdminUser.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    
    # Check email taken in DB
    existing_email = await db.execute(select(AdminUser).where(AdminUser.email == body.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    # Generate OTP
    otp = _generate_otp()
    expiry = time.time() + OTP_TTL
    
    # Store pending registration
    _pending_registrations[body.username] = {
        "name": body.name,
        "email": body.email,
        "password_hash": _hash_password(body.password),
        "expiry": expiry,
        "otp": otp
    }
    
    _otp_store[body.username] = (otp, expiry)
    background_tasks.add_task(_send_otp_email, body.email, body.username, otp)

    return OTPSentResponse(
        message="OTP sent for verification",
        masked_email=_mask_email(body.email),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Direct login with username and password."""
    result = await db.execute(select(AdminUser).where(AdminUser.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not _verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    
    logger.info(f"Admin logged in: {user.username}")
    return TokenResponse(
        token=_make_token(user),
        username=user.username,
        name=user.name or user.username,
        email=user.email,
        role=user.role,
    )


@router.post("/send-otp", response_model=OTPSentResponse)
async def send_otp(body: SendOTPRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Resend OTP for a pending registration or login (if needed, but mainly registration now)."""
    # For registration resend, we check the pending store
    pending = _pending_registrations.get(body.username)
    if not pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No pending registration found for this user")

    otp = _generate_otp()
    pending["otp"] = otp
    pending["expiry"] = time.time() + OTP_TTL
    _otp_store[body.username] = (otp, pending["expiry"])
    
    background_tasks.add_task(_send_otp_email, pending["email"], body.username, otp)

    return OTPSentResponse(
        message="New OTP sent successfully",
        masked_email=_mask_email(pending["email"]),
    )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(body: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Validate OTP and FINALLY create the user in the database."""
    pending = _pending_registrations.get(body.username)
    if not pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No pending registration found")

    if time.time() > pending["expiry"]:
        del _pending_registrations[body.username]
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "OTP has expired. Please register again.")
    
    if not hmac.compare_digest(body.otp.strip(), pending["otp"]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OTP")

    # OTP valid — Create user in DB
    user = AdminUser(
        name=pending["name"],
        username=body.username,
        email=pending["email"],
        password_hash=pending["password_hash"],
        role="admin",
        created_at=time.time(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Cleanup stores
    del _pending_registrations[body.username]
    if body.username in _otp_store:
        del _otp_store[body.username]

    logger.info(f"New admin verified and created: {user.username}")
    return TokenResponse(
        token=_make_token(user),
        username=user.username,
        name=user.name or user.username,
        email=user.email,
        role=user.role,
    )

