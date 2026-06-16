"""
Gantabya Travel Booking System - Configuration File
This file contains all configuration settings for the Flask application.
"""

import os
from datetime import timedelta

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration class"""
    
    # ==================== DATABASE CONFIGURATION ====================
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///gantabya.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # ==================== SECURITY CONFIGURATION ====================
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gantabya-super-secret-key-2024'
    
    # Password hashing configuration
    BCRYPT_LOG_ROUNDS = 13
    BCRYPT_HASH_PREFIX = b'2b'
    
    # ==================== SESSION CONFIGURATION ====================
    # Session settings
    SESSION_COOKIE_NAME = 'gantabya_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # ==================== FILE UPLOAD CONFIGURATION ====================
    # Upload folder for package images
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # ==================== MAIL CONFIGURATION (for future email features) ====================
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@gantabya.com'
    
    # ==================== PAGINATION ====================
    ITEMS_PER_PAGE = 12
    ADMIN_ITEMS_PER_PAGE = 20
    
    # ==================== CACHE CONFIGURATION ====================
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # ==================== API CONFIGURATION ====================
    # For future API integrations (payment gateway, flight API, etc.)
    PAYMENT_API_KEY = os.environ.get('PAYMENT_API_KEY') or ''
    FLIGHT_API_KEY = os.environ.get('FLIGHT_API_KEY') or ''
    HOTEL_API_KEY = os.environ.get('HOTEL_API_KEY') or ''
    
    # ==================== APPLICATION SETTINGS ====================
    # Application name and details
    APP_NAME = "Gantabya Travel"
    APP_DESCRIPTION = "Your Journey Begins Here"
    APP_VERSION = "1.0.0"
    
    # Admin email for error notifications
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@gantabya.com'
    
    # ==================== CSRF PROTECTION ====================
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-gantabya-secret-key'
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # ==================== DEBUGGING ====================
    DEBUG = False
    TESTING = False
    PROPAGATE_EXCEPTIONS = True
    
    # ==================== LOGGING ====================
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(basedir, 'logs', 'app.log')
    
    # ==================== RATE LIMITING (for future) ====================
    RATELIMIT_ENABLED = False
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = "memory://"


class DevelopmentConfig(Config):
    """Development configuration - used during development"""
    
    DEBUG = True
    TESTING = False
    
    # Use SQLite for development (simpler)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///gantabya.db'
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # Session settings for development
    SESSION_COOKIE_SECURE = False
    
    # Logging for development
    LOG_LEVEL = 'DEBUG'
    
    # Disable CSRF for development (optional, enable in production)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False


class ProductionConfig(Config):
    """Production configuration - used when deployed"""
    
    DEBUG = False
    TESTING = False
    
    # Use PostgreSQL in production (change as needed)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/gantabya'
    
    # Session settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Logging for production
    LOG_LEVEL = 'WARNING'
    
    # Rate limiting for production
    RATELIMIT_ENABLED = True


class TestingConfig(Config):
    """Testing configuration - used for unit tests"""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Session settings for testing
    SESSION_COOKIE_SECURE = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment variable"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])