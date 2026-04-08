"""
Configuration management for OpenEnv Email Triage.

Handles environment variables, application settings, and feature flags.
"""

import os
import logging
from enum import Enum

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
RELOAD = os.getenv("RELOAD", "true").lower() == "true" if ENVIRONMENT == "development" else False

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

# API
API_TITLE = "📧 OpenEnv Email Triage"
API_VERSION = "2.0"
API_DESCRIPTION = "Intelligent customer support workflow simulator"

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"

# Environment settings
class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings:
    """Application settings"""
    
    # API Configuration
    api_title: str = API_TITLE
    api_version: str = API_VERSION
    api_description: str = API_DESCRIPTION
    
    # Server
    host: str = HOST
    port: int = PORT
    reload: bool = RELOAD
    environment: str = ENVIRONMENT
    debug: bool = DEBUG
    
    # Email processing
    max_steps: int = 100
    reward_weights: dict = {
        "classify_correct": 0.2,
        "prioritize_correct": 0.2,
        "respond": 0.4,
        "close": 0.2,
        "step_penalty": -0.05
    }
    
    # Grading
    grading_weights: dict = {
        "accuracy": 0.35,
        "priority": 0.25,
        "response": 0.20,
        "efficiency": 0.20
    }
    
    # Performance thresholds
    performance_thresholds: dict = {
        "s_tier": 90,
        "a_tier": 80,
        "b_tier": 70,
        "c_tier": 60
    }
    
    @classmethod
    def get_log_config(cls):
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": LOG_LEVEL,
                    "formatter": "default",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": LOG_LEVEL,
                    "formatter": "detailed",
                    "filename": LOG_FILE,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "root": {
                "level": LOG_LEVEL,
                "handlers": ["console", "file"]
            }
        }


# Create settings instance
settings = Settings()


def get_settings():
    """Get application settings"""
    return settings


def is_production():
    """Check if running in production"""
    return settings.environment == EnvironmentType.PRODUCTION.value


def is_development():
    """Check if running in development"""
    return settings.environment == EnvironmentType.DEVELOPMENT.value
