from os import environ
from pathlib import Path

basedir = Path(__file__).resolve().parent.parent


class Config:
    """Set Flask config variables."""

    # General Config
    ENVIRONMENT = environ.get("ENVIRONMENT", "development")
    FLASK_APP = environ.get("FLASK_APP", "radio_browser")
    FLASK_DEBUG = environ.get("FLASK_DEBUG", False)
    SECRET_KEY = environ.get("SECRET_KEY", "dev")
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"

    # Database
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///radio_browser.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS Secrets
    AWS_SECRET_KEY = environ.get("AWS_SECRET_KEY", "")
    AWS_KEY_ID = environ.get("AWS_KEY_ID", "")
