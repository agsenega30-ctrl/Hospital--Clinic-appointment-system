import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "hospital-secure-default-key-change-in-prod-2026")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/hospital_appointment_system")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "hospital_appointment_system")
    MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "2000"))
    MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "2000"))
    ENABLE_EMBEDDED_FALLBACK = os.getenv("ENABLE_EMBEDDED_FALLBACK", "True").lower() in ("true", "1", "yes")

    # Timezone
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")

    # Security & Session Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    # Initial Admin Setup Defaults (Used for seeding)
    INITIAL_ADMIN_EMAIL = os.getenv("INITIAL_ADMIN_EMAIL", "admin@hospital.com")
    INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin@Hospital2026")
    INITIAL_ADMIN_NAME = os.getenv("INITIAL_ADMIN_NAME", "System Administrator")

    # Rate Limiting
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key-hospital-system"
    MONGO_URI = "mongomock://localhost/test_hospital_db"
    MONGO_DB_NAME = "test_hospital_db"
