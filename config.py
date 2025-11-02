import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    UPLOAD_FOLDER = 'storage/uploads'
    OWNER_FOLDER = 'storage/owner'
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'mkv', 'webm', 'avi'}
    MAX_VIDEO_DURATION = 120  # 2 minutes in seconds
    
    # No Redis/Celery needed
    USE_BACKGROUND_THREADS = True

def create_folders():
    """Create necessary folders if they don't exist"""
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.OWNER_FOLDER, exist_ok=True)