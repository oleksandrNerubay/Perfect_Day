import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI        = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB         = os.getenv("MONGO_DB", "perfectday")
ML_SERVICE_URL   = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
ASR_PROVIDER     = os.getenv("ASR_PROVIDER", "deepgram")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
WHISPER_MODEL    = os.getenv("WHISPER_MODEL", "base")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-in-prod")
