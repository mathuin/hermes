from datetime import date, time

import pytest

from radio_browser import create_app
from radio_browser.enum import DayOfWeek, EmissionType
from radio_browser.extensions import db
from radio_browser.models import Frequency, MapArea, Schedule, Station, TimeList, TimeRange, Transmission


@pytest.fixture(scope="function")
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})

    with app.app_context():
        db.drop_all()
        db.create_all()
        # the test does the rest
        yield app
        db.session.remove()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def session(app):
    with app.app_context():
        db.session.begin_nested()
        yield db.session
        db.session.rollback()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def schedule(session):
    schedule = Schedule(name="Test Schedule", date=date(2024, 11, 20), source_url="http://example.com/")
    session.add(schedule)
    session.commit()
    return schedule


@pytest.fixture
def station(schedule, session):
    station = Station(
        schedule=schedule,
        callsign="Test Station",
        location="Test Location",
        region="Test Region",
    )
    schedule.stations.append(station)
    session.add(schedule)
    session.commit()
    return station


@pytest.fixture
def frequency(station, session):
    frequency = Frequency(
        station=station,
        value=123.4,
    )
    station.frequencies.append(frequency)
    session.add(station)
    session.commit()
    return frequency


@pytest.fixture
def timerange(frequency, session):
    timerange = TimeRange(frequency=frequency, start=time(0, 0), end=time(1, 0))
    frequency.times.append(timerange)
    session.add(frequency)
    session.commit()
    return timerange


@pytest.fixture
def map_area(station, session):
    map_area = MapArea(station=station, ident="ID", description="Test Description")
    station.map_areas.append(map_area)
    session.add(station)
    session.commit()
    return map_area


@pytest.fixture
def transmission(map_area, station, session):
    transmission = Transmission(
        station=station,
        title="Test Title",
        times=None,
        emissions=[EmissionType.A1A],
        days=[DayOfWeek.Mon, DayOfWeek.Tue],
        map_area=map_area,
    )
    station.transmissions.append(transmission)
    session.add(station)
    session.commit()
    return transmission


@pytest.fixture
def timelist(transmission, session):
    timelist = TimeList(transmission=transmission, initial=time(0, 30), rebroadcast=time(12, 30), valid=time(0, 0))
    transmission.times.append(timelist)
    session.add(transmission)
    session.commit()
    return timelist
