import os
import sys
from dotenv import load_dotenv
import asyncio

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from backend.routers.auth import _send_otp_email

print("Testing _send_otp_email...")
try:
    _send_otp_email("gupta.pankaj8818@gmail.com", "Pankaj", "123456")
    print("Success calling _send_otp_email")
except Exception as e:
    print(f"Error: {e}")
