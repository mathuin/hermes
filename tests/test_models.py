from datetime import time

from hermes.enum import EmissionType
from hermes.models import TimeRange, Transmission


def test_schedule_creation(schedule):
    assert schedule.id is not None
    assert schedule.name == "Test Schedule"


def test_station_creation(schedule, station):
    assert station.id is not None
    assert station.schedule_id == schedule.id
    assert station.callsign == "Test Station"


def test_frequency_creation(frequency, station):
    assert frequency.id is not None
    assert frequency.station_id == station.id
    assert frequency.value == 123.4


def test_map_area_creation(station, map_area):
    assert map_area.id is not None
    assert map_area.station_id == station.id


def test_transmission_creation(map_area, transmission, station, session):
    assert transmission.id is not None
    assert transmission.station_id == station.id
    assert transmission.title == "Test Title"

    # not all transmissions have valid map areas
    try:
        _ = Transmission(
            station=station,
            title="Test Title",
        )
    except ValueError as exc:
        raise AssertionError("transmissions without map areas should not raise here") from exc


def test_station_get_frequencies_at_time_empty_timerange(frequency, station):
    actual = station.get_frequencies_at_time(time(12, 30))
    assert isinstance(actual, list)
    assert len(actual) == 1
    assert actual[0].value == 123.4


def test_station_get_frequencies_at_time(frequency, timerange, station):
    actual = station.get_frequencies_at_time(time(0, 30))
    assert isinstance(actual, list)
    assert len(actual) == 1
    assert actual[0].value == 123.4
    actual = station.get_frequencies_at_time(time(12, 30))
    assert isinstance(actual, list)
    assert len(actual) == 0


def test_station_get_frequencies_cross_midnight(frequency, station, session):
    timerange = TimeRange(frequency=frequency, start=time(23, 0), end=time(2, 0))
    frequency.times.append(timerange)
    session.add(frequency)
    session.commit()
    actual = station.get_frequencies_at_time(time(0, 30))
    assert isinstance(actual, list)
    assert len(actual) == 1
    assert actual[0].value == 123.4
    actual = station.get_frequencies_at_time(time(12, 30))
    assert isinstance(actual, list)
    assert len(actual) == 0
