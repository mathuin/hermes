from datetime import time
from pprint import pprint

from hermes.enum import DayOfWeek, EmissionType
from hermes.filter import DateTimeRange, get_emissions, get_events
from hermes.models import Frequency, TimeList, Transmission


def test_in_range_same_day():
    dtr = DateTimeRange(DayOfWeek.Mon, time(10, 0), time(18, 0))
    assert dtr.in_range(DayOfWeek.Mon, time(12, 0)) is True
    assert dtr.in_range(DayOfWeek.Mon, time(9, 0)) is False


def test_in_range_across_days():
    dtr = DateTimeRange(DayOfWeek.Mon, time(22, 0), time(6, 0))
    assert dtr.in_range(DayOfWeek.Mon, time(23, 0)) is True
    assert dtr.in_range(DayOfWeek.Tue, time(5, 0)) is True
    assert dtr.in_range(DayOfWeek.Tue, time(7, 0)) is False


def test_in_range_wrap_around():
    dtr = DateTimeRange(DayOfWeek.Sat, time(23, 30), time(1, 30))
    assert dtr.in_range(DayOfWeek.Sat, time(23, 59)) is True
    assert dtr.in_range(DayOfWeek.Sun, time(0, 30)) is True
    assert dtr.in_range(DayOfWeek.Sun, time(2, 0)) is False


def test_in_range_exact_boundary():
    dtr = DateTimeRange(DayOfWeek.Fri, time(8, 0), time(18, 0))
    assert dtr.in_range(DayOfWeek.Fri, time(8, 0)) is True
    assert dtr.in_range(DayOfWeek.Fri, time(18, 0)) is True
    assert dtr.in_range(DayOfWeek.Fri, time(7, 59)) is False
    assert dtr.in_range(DayOfWeek.Fri, time(18, 1)) is False


def test_get_emissions(schedule, station, frequency, transmission, session):
    actual = get_emissions(station, transmission, [frequency])
    assert actual == transmission.emissions
    transmission.emissions = []
    session.add(transmission)
    session.commit()
    actual = get_emissions(station, transmission, [frequency])
    assert actual == []
    station.emissions = [EmissionType.J3C]
    session.add(station)
    session.commit()
    actual = get_emissions(station, transmission, [frequency])
    assert actual == station.emissions
    frequency.emissions = [EmissionType.A3E]
    session.add(station)
    session.commit()
    actual = get_emissions(station, transmission, [frequency])
    assert actual == frequency.emissions


def test_get_events(schedule, station, frequency, transmission, map_area, timelist, timerange):
    in_range_dtr = DateTimeRange(DayOfWeek.Mon, time(0, 0), time(1, 0))
    events = get_events(in_range_dtr, [station])
    assert isinstance(events, list)
    assert len(events) == 1
    event = events[0]
    assert event.day == DayOfWeek.Mon
    assert event.time == time(0, 30)
    assert event.name == "Test Title (A1A)"
    assert isinstance(event.frequencies, list)
    assert len(event.frequencies) == 1
    freq = event.frequencies[0]
    assert freq == 123.4
    out_of_range_dtr = DateTimeRange(DayOfWeek.Mon, time(12, 0), time(13, 0))
    events = get_events(out_of_range_dtr, [station])
    assert isinstance(events, list)
    assert len(events) == 0


def test_get_events_no_timerange(schedule, station, frequency, transmission, map_area, timelist):
    dtr = DateTimeRange(DayOfWeek.Mon, time(0, 0), time(1, 0))
    events = get_events(dtr, [station])
    assert isinstance(events, list)
    assert len(events) == 1
