import json

from hermes import create_app
from hermes.extensions import db
from hermes.schemas import schedule as schedule_schema


def test_config():
    assert not create_app().testing
    assert create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory"}).testing
