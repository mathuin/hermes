from hermes import schemas


def test_schedule(schedule):
    actual = schemas.schedule.dump(schedule)
    assert actual["date"] == "2024-11-20"


def test_station(station):
    actual = schemas.station.dump(station)
    assert actual["callsign"] == "Test Station"


def test_frequency(frequency, timerange):
    actual = schemas.frequency.dump(frequency)
    assert actual["times"] == [schemas.timerange.dump(timerange)]


def test_transmission(transmission):
    actual = schemas.transmission.dump(transmission)
    assert actual["emissions"] == ["A1A"]


def test_map_area(map_area):
    actual = schemas.map_area.dump(map_area)
    assert actual["ident"] == "ID"
