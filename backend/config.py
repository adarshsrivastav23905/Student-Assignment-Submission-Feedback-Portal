"""
Configuration Module
====================
Loads all application settings from environment variables.
Provides sensible defaults for local development.
Never hardcodes secrets — uses .env file via python-dotenv.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # --- Flask Settings ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # --- JWT Settings ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    )

    # --- Database Settings ---
    # Local: SQLite | Cloud: PostgreSQL connection string
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///assignment_portal.db")

    # --- Storage Settings ---
    # "local" for filesystem, "cloud" for cloud object storage
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    LOCAL_UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", "uploads")

    # Cloud storage settings (Firebase/Supabase/S3)
    CLOUD_STORAGE_BUCKET = os.getenv("CLOUD_STORAGE_BUCKET", "")
    CLOUD_STORAGE_KEY = os.getenv("CLOUD_STORAGE_KEY", "")

    # --- File Upload Settings ---
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = os.getenv(
        "ALLOWED_EXTENSIONS", "pdf,docx,doc,txt,zip,png,jpg,jpeg"
    ).split(",")

    # --- CORS Settings ---
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500").split(",")

    # --- Server Settings ---
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # --- Rate Limiting ---
    RATE_LIMIT = os.getenv("RATE_LIMIT", "100/hour")

    # --- Logging ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URL = "sqlite:///test_assignment_portal.db"
    LOCAL_UPLOAD_DIR = "test_uploads"


# Configuration map
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
