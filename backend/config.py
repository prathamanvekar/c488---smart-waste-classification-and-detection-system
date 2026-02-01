"""
Configuration Module
Application configuration and environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)  # Force .env to override system vars

# Debug: Print loaded values
print(f"[DEBUG] Loading .env from: {env_path}")
print(f"[DEBUG] PORT from env: {os.getenv('PORT', 'NOT SET')}")
print(f"[DEBUG] HOST from env: {os.getenv('HOST', 'NOT SET')}")


class Config:
    """Application configuration"""

    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5001))

    # File upload settings
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 16777216))  # 16MB default
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'webp'}

    # Model settings
    MODEL_PATH = os.getenv('MODEL_PATH', 'best.pt')
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.25))

    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(BASE_DIR, 'waste.db'))

    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')


# Create uploads directory if it doesn't exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
