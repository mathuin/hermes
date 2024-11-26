from datetime import date as dtdate
from datetime import datetime, time

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKeyConstraint

from radio_browser.enum import DayOfWeek, EmissionType, Enums
from radio_browser.extensions import date_format, db, time_format


class Schedule(db.Model):  # type: ignore[name-defined]
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    date: Mapped[dtdate]
    source_url: Mapped[str | None]

    stations: Mapped[list["Station"]] = relationship(back_populates="schedule")

    __table_args__ = (UniqueConstraint("name", "date", name="unique_name_date"),)

    def __init__(self, name, date, source_url=None):
        self.name = name
        self.date = datetime.strptime(date, date_format).date() if type(date) == str else date
        self.source_url = source_url


class Station(db.Model):  # type: ignore[name-defined]
    __tablename__ = "station"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedule.id"))
    schedule: Mapped["Schedule"] = relationship(back_populates="stations")

    callsign: Mapped[str]
    location: Mapped[str]
    region: Mapped[str | None]
    emissions: Mapped[list[EmissionType]] = mapped_column(Enums(EmissionType))

    frequencies: Mapped[list["Frequency"]] = relationship(back_populates="station")
    transmissions: Mapped[list["Transmission"]] = relationship(back_populates="station")
    map_areas: Mapped[list["MapArea"]] = relationship(back_populates="station")

    __table_args__ = (UniqueConstraint("schedule_id", "callsign", name="unique_schedule_id_callsign"),)

    def __init__(self, schedule, callsign, location, region=None, emissions=None):
        self.schedule_id = schedule.id
        self.callsign = callsign
        self.location = location
        self.region = region
        self.emissions = emissions or []

    def get_frequencies_at_time(self, reference_time: time):
        in_use_frequencies = []
        for frequency in self.frequencies:
            if frequency.times == []:
                in_use_frequencies.append(frequency)
                continue
            for time_range in frequency.times:
                if time_range.start <= time_range.end:
                    # Standard case: start and end are on the same day
                    if time_range.start <= reference_time <= time_range.end:
                        in_use_frequencies.append(frequency)
                        break
                else:
                    # Spans midnight: two conditions to check
                    if reference_time >= time_range.start or reference_time <= time_range.end:
                        in_use_frequencies.append(frequency)
                        break
        return in_use_frequencies


class Frequency(db.Model):  # type: ignore[name-defined]
    __tablename__ = "frequency"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("station.id"))
    station: Mapped["Station"] = relationship(back_populates="frequencies")

    value: Mapped[float]
    callsign: Mapped[str | None]
    emissions: Mapped[list[EmissionType]] = mapped_column(Enums(EmissionType))
    times: Mapped[list["TimeRange"]] = relationship(back_populates="frequency")
    power: Mapped[float | None]

    __table_args__ = (UniqueConstraint("station_id", "value", name="unique_station_id_value"),)

    def __init__(self, station, value, callsign=None, emissions=None, times=None, power=None):
        self.station_id = station.id
        self.value = value
        self.callsign = callsign
        self.emissions = emissions or []
        self.times = times or []
        self.power = power


class Transmission(db.Model):  # type: ignore[name-defined]
    __tablename__ = "transmission"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("station.id"))
    station: Mapped["Station"] = relationship(back_populates="transmissions")

    title: Mapped[str]
    times: Mapped[list["TimeList"]] = relationship(back_populates="transmission")
    emissions: Mapped[list[EmissionType]] = mapped_column(Enums(EmissionType))
    days: Mapped[list[DayOfWeek]] = mapped_column(Enums(DayOfWeek))

    map_area_id: Mapped[int | None] = mapped_column(ForeignKey("map_area.id"))

    __table_args__ = (
        ForeignKeyConstraint(
            ["map_area_id", "station_id"],
            ["map_area.id", "map_area.station_id"],
        ),
    )

    def __init__(self, station, title, times=None, emissions=None, days=None, map_area=None):
        self.station_id = station.id
        self.title = title
        self.times = times or []
        self.emissions = emissions or []
        self.days = days or list(DayOfWeek)
        self.map_area_id = None if map_area is None else map_area.id


class MapArea(db.Model):  # type: ignore[name-defined]
    __tablename__ = "map_area"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("station.id"))
    station: Mapped["Station"] = relationship(back_populates="map_areas")

    ident: Mapped[str]
    description: Mapped[str]

    __table_args__ = (UniqueConstraint("station_id", "ident", name="unique_station_id_ident"),)

    def __init__(self, station, ident, description):
        self.station_id = station.id
        self.ident = ident
        self.description = description


class TimeRange(db.Model):  # type: ignore[name-defined]
    __tablename__ = "time_range"

    id: Mapped[int] = mapped_column(primary_key=True)
    frequency_id: Mapped[int] = mapped_column(ForeignKey("frequency.id"))
    frequency: Mapped["Frequency"] = relationship(back_populates="times")

    start: Mapped[time]
    end: Mapped[time]

    def __init__(self, frequency, start, end):
        self.frequency_id = frequency.id
        self.start = datetime.strptime(start, time_format).time() if type(start) == str else start
        self.end = datetime.strptime(end, time_format).time() if type(end) == str else end


class TimeList(db.Model):  # type: ignore[name-defined]
    __tablename__ = "times"

    id: Mapped[int] = mapped_column(primary_key=True)
    transmission_id: Mapped[int] = mapped_column(ForeignKey("transmission.id"))
    transmission: Mapped["Transmission"] = relationship(back_populates="times")

    initial: Mapped[time]
    rebroadcast: Mapped[time | None]
    valid: Mapped[time | None]

    def __init__(self, transmission, initial, rebroadcast=None, valid=None):
        self.transmission_id = transmission.id
        self.initial = datetime.strptime(initial, time_format).time() if type(initial) == str else initial
        self.rebroadcast = (
            datetime.strptime(rebroadcast, time_format).time() if type(rebroadcast) == str else rebroadcast
        )
        self.valid = datetime.strptime(valid, time_format).time() if type(valid) == str else valid
