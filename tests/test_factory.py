import json

from radio_browser import create_app
from radio_browser.extensions import db
from radio_browser.schemas import schedule as schedule_schema


def test_config():
    assert not create_app().testing
    assert create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory"}).testing
