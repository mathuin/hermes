from datetime import datetime, time
from typing import ClassVar

from radio_browser.enum import DayOfWeek, EmissionType
from radio_browser.extensions import time_format
from radio_browser.models import Frequency, Station, Transmission


class DateTimeRange:
    def __init__(self, day: DayOfWeek, start_time: time, end_time: time):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time

    def in_range(self, check_day: DayOfWeek, check_time: time) -> bool:
        if self.start_time < self.end_time:
            return self.day == check_day and self.start_time <= check_time <= self.end_time
        else:
            if self.day == check_day and check_time >= self.start_time:
                return True
            next_day = self.day.next()
            if next_day == check_day and check_time <= self.end_time:
                return True
        return False


class Event:
    day_order: ClassVar = list(DayOfWeek)
    day_indices: ClassVar = {day: i for i, day in enumerate(day_order)}

    def __init__(self, day: DayOfWeek, time: time, name: str, station: str, frequencies: list[float]):
        self.day = day
        self.time = time
        self.name = name
        self.station = station
        self.frequencies = frequencies

    @staticmethod
    def sort_key(event: "Event") -> tuple:
        day_idx = Event.day_indices[event.day]
        return (day_idx, event.time)


def get_emissions(station: Station, transmission: Transmission, frequencies: list[Frequency]) -> list[EmissionType]:
    emissions = []

    if station.emissions:
        emissions = station.emissions
    if transmission.emissions:
        emissions = transmission.emissions
    frequency_emissions = {emission for frequency in frequencies for emission in frequency.emissions}
    if frequency_emissions:
        emissions = list(frequency_emissions)
    return emissions


def get_events(dtr: DateTimeRange, stations: list[Station]) -> list[Event]:
    events: list[Event] = []

    for station in stations:
        transmissions = Transmission.query.filter(Transmission.station_id == station.id).all()
        for transmission in transmissions:
            for day in transmission.days:
                for timelist in transmission.times:
                    if dtr.in_range(day, timelist.initial):
                        freqs = station.get_frequencies_at_time(timelist.initial)
                        emissions = get_emissions(station, transmission, freqs)
                        name = (
                            f"{transmission.title} ({', '.join([e.value for e in emissions])})"
                            if emissions
                            else transmission.title
                        )
                        tag = f"{station.callsign} ({station.location})"
                        frequencies = [freq.value for freq in freqs]
                        new_event = Event(day, timelist.initial, name, tag, frequencies)
                        events.append(new_event)

    events.sort(key=Event.sort_key)
    return events
