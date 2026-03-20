import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_ADDRESS  = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if TELEGRAM_TOKEN is None:
    raise ValueError("Missing TELEGRAM_TOKEN in .env")

if OPENAI_API_KEY is None:
    print("Warning: OPENAI_API_KEY not set (LLM features disabled)")

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    print("Warning: EMAIL_ADDRESS / EMAIL_PASSWORD not set (email features disabled)")
