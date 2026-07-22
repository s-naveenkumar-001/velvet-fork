import os
import secrets

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_FALLBACK_MODEL = os.environ.get("OPENROUTER_FALLBACK_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///restaurant.db")

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
