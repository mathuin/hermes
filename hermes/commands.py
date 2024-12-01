import json
import os
import re
from collections import defaultdict
from contextlib import suppress
from datetime import date, datetime, time

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError

from hermes.extensions import date_format, db
from hermes.models import Frequency, MapArea, Schedule, Station, TimeList, TimeRange, Transmission
from hermes.schemas import frequency as frequency_schema
from hermes.schemas import map_area as map_area_schema
from hermes.schemas import schedule as schedule_schema
from hermes.schemas import station as station_schema
from hermes.schemas import transmission as transmission_schema


@click.command("init-db")
@click.option("--drop", is_flag=True, help="Drop existing tables before creating new ones.")
def init_db(drop):
    if drop:
        db.drop_all()
        click.echo("Dropped all tables.")
    db.create_all()
    click.echo("Database initialized successfully!")


@click.command("load-schedule")
@click.argument("json_file", type=click.Path(exists=True))
@with_appcontext
def load_schedule(json_file):
    try:
        with open(json_file) as file:
            schedule_data = json.load(file)
        stations_data = schedule_data.pop("stations", [])
        schedule = Schedule(
            name=schedule_data["name"], date=schedule_data["date"], source_url=schedule_data.get("source_url", None)
        )
        db.session.add(schedule)

        for station_data in stations_data:
            map_areas_data = station_data.pop("map_areas", [])
            frequencies_data = station_data.pop("frequencies", [])
            transmissions_data = station_data.pop("transmissions", [])

            station = Station(
                schedule=schedule,
                callsign=station_data["callsign"],
                location=station_data["location"],
                region=station_data.get("region", None),
                emissions=station_data.get("emissions", None),
            )
            schedule.stations.append(station)
            db.session.add(schedule)

            for map_area_data in map_areas_data:
                map_area = MapArea(
                    station=station,
                    ident=map_area_data["ident"],
                    description=map_area_data["description"],
                )
                station.map_areas.append(map_area)
                db.session.add(station)

            for frequency_data in frequencies_data:
                timeranges_data = frequency_data.pop("times", [])
                frequency = Frequency(
                    station=station,
                    value=frequency_data["value"],
                    callsign=frequency_data.get("callsign", None),
                    emissions=frequency_data.get("emissions", None),
                    times=None,
                    power=frequency_data.get("power", None),
                )
                db.session.add(frequency)

                for timerange_data in timeranges_data:
                    timerange = TimeRange(
                        frequency=frequency,
                        start=timerange_data["start"],
                        end=timerange_data["end"],
                    )
                    frequency.times.append(timerange)
                station.frequencies.append(frequency)
                db.session.add(station)

            for transmission_data in transmissions_data:
                map_area = None  # query for the map area somehow
                timelists_data = transmission_data.pop("times", [])
                transmission = Transmission(
                    station=station,
                    title=transmission_data["title"],
                    times=None,
                    emissions=transmission_data.get("emissions", None),
                    days=transmission_data.get("days", None),
                    map_area=map_area,
                )
                db.session.add(transmission)

                for timelist_data in timelists_data:
                    timelist = TimeList(
                        transmission=transmission,
                        initial=timelist_data["initial"],
                        rebroadcast=timelist_data.get("rebroadcast", None),
                        valid=timelist_data.get("valid", None),
                    )
                    transmission.times.append(timelist)
                station.transmissions.append(transmission)
                db.session.add(station)
        db.session.commit()
        click.echo(f"Schedule '{schedule.name}' loaded successfully.")
    except IntegrityError as e:
        click.echo(f"IntegrityError: {e}", err=True)
    except Exception as e:  # pragma: no cover
        db.session.rollback()
        click.echo(f"Failed to load schedule: {e}", err=True)


def number_from_string(string: str):
    return int(string) if string.isdigit() else float(string)


@click.command("make-arrl-schedule")
@click.argument("bulletin", type=click.Path(exists=True))
@with_appcontext
def make_arrl_schedule(bulletin):
    with open(bulletin) as file:
        lines = [line.strip() for line in file]

    schedule_dict = {"name": "arrl", "date": None, "source_url": None}
    station_dict = {"callsign": None, "location": None}
    transmissions_list = []

    # patterns
    callsign_pattern = re.compile(r"^QST de ([0-9A-Z]*)$")
    location_date_pattern = re.compile(r"^([A-Za-z,]* [A-Z]{2}) *([A-Za-z]* [0-9]*, [0-9]*)$")
    source_url_pattern = re.compile(r"(https?:[^ ]*)")
    frequency_pattern = re.compile(r"([A-Z]+):(?:\s*-)?\s*([\d\s\.\-]*)")
    reset_pattern = re.compile(r"Schedule:")
    exit_pattern = re.compile(r"Notes:")
    event_pattern = re.compile(r"([0-9]{4}) ((UTC)|( \" )) ((\([0-9 A-Z:]*\))|( *\")) *([A-Z]{2,})([a-z]?) *(.*)")

    # modes
    mode_emissions = {
        "CW": ["A1A"],
        "DIGITAL": ["F1B", "J2B"],
        "VOICE": ["J3E"],
    }
    mode_titles = {
        "CWf": "Fast Code",
        "CWs": "Slow Code",
        "CWb": "Code Bulletin",
        "DIGITAL": "Digital Bulletin",
        "VOICE": "Voice Bulletin",
    }
    mode_keys = mode_emissions.keys()
    mode_values = {mode: [] for mode in mode_keys}
    mode_times = {mode: [] for mode in mode_keys}

    # flags
    last_mode = None
    start_time = None
    end_time = None

    # iterate through all the lines
    for line in lines:
        match = re.search(callsign_pattern, line)
        if match:
            station_dict["callsign"] = match.group(1)
            continue
        match = re.search(location_date_pattern, line)
        if match:
            station_dict["location"] = match.group(1)
            date_string = match.group(2)
            schedule_dict["date"] = datetime.strptime(date_string, "%B %d, %Y").date()
            continue
        match = re.search(source_url_pattern, line)
        if match:
            schedule_dict["source_url"] = match.group(1)
            continue
        match = re.search(frequency_pattern, line)
        if match:
            key, values = match.groups()
            mode_values[key] = [1000 * number_from_string(value) for value in values.split(" ")]
            continue

        # build timeranges for frequencies
        match = re.search(reset_pattern, line)
        if match:
            if last_mode is not None:
                mode_times[last_mode].append({"start": start_time, "end": end_time})
            last_mode = None
            start_time = None
            end_time = None
            continue
        match = re.search(exit_pattern, line)
        if match:
            mode_times[last_mode].append({"start": start_time, "end": end_time})
            continue
        match = re.search(event_pattern, line)
        if match:
            # first frequency state machine
            new_time = match.group(1)
            new_mode = match.group(8)
            if last_mode is None:
                last_mode = new_mode
                start_time = new_time
                end_time = new_time
            elif last_mode == new_mode:
                end_time = new_time
            else:
                mode_times[last_mode].append({"start": start_time, "end": end_time})
                last_mode = new_mode
                start_time = new_time
                end_time = new_time
            # now do transmission stuff
            new_days = match.group(10)
            if new_days == "Daily":
                new_days = "Mon, Tue, Wed, Thu, Fri"
            transmission_dict = {
                "times": [{"initial": new_time}],
                "emissions": mode_emissions[new_mode],
                "days": new_days.split(", "),
                "title": mode_titles[f"{match.group(8)}{match.group(9)}"],
            }
            transmissions_list.append(transmission_dict)
            continue

    # Deduplicate and merge
    merged = defaultdict(list)
    for mode in mode_keys:
        for mode_value in mode_values[mode]:
            merged[mode_value].extend(mode_times[mode])
    frequencies_list = [{"value": value, "times": times} for value, times in merged.items()]

    # The web version of the schedule includes the following as of Nov 2024:
    # Voice transmissions on 7.290 MHz are in AM, double-sideband full-carrier.
    for frequency in frequencies_list:
        if frequency["value"] == 7290.0:
            frequency["emissions"] = ["A3E"]

    station_dict["frequencies"] = frequencies_list
    station_dict["transmissions"] = transmissions_list
    schedule_dict["stations"] = [station_dict]

    schedule_dict["date"] = schedule_dict["date"].strftime(date_format)

    print(json.dumps(schedule_dict))


@click.command("make-wefax-schedule")
@click.argument("sources", nargs=-1, type=click.Path(exists=True))
@with_appcontext
def make_wefax_schedule(sources):
    # Date used will be the latest 'Information dated' date.
    schedule_dict = {
        "name": "wefax",
        "date": None,
        "source_url": "https://www.weather.gov/media/marine/rfax.pdf",
        "stations": [],
    }
    latest_date = date(1970, 1, 1)

    # patterns
    frequency_pattern = re.compile(
        r"^([A-Z0-9]*| ) *([0-9.]*) *kHz *(ALL BROADCAST TIMES|[0-9z-]*) *([A-Z][0-9][A-Z]) *([0-9]*)"
    )
    times_pattern = re.compile(r"(\d{4})z?-(\d{4})")
    transmission_data_pattern = re.compile(
        r"([0-9]{4}|-{4})/([0-9]{4}|-{4}) *(.*[A-Za-z0-9\)]) *[0-9]{3}/[0-9]{3} *(LATEST|[0-9]{4}|[0-9]{2}/[0-9]{2})[ \t]*([A-Z0-9/]*)"
    )
    transmission_test_pattern = re.compile(r"([0-9]{4}|-{4})/([0-9]{4}|-{4}) *(.*[A-Za-z0-9\)])( *[0-9]{3}/[0-9]{3})?")
    map_area_most_pattern = re.compile(
        r"([0-9A-Z])\. *([0-9A-Z][0-9A-Z, -]*[A-Z])[ \t]*([0-9A-Z]{1,2})\. *([0-9A-Z][0-9A-Z, -]*[0-9A-Z])"
    )
    map_area_gulf_pattern = re.compile(r"([0-9A-Z])\. *([0-9A-Z][0-9A-Z, -]*)")

    # state abbreviations (add as necessary)
    states = {
        "ALASKA": "AK",
        "LOUISIANA": "LA",
        "HAWAII": "HI",
        "MASSACHUSETTS": "MA",
        "CALIFORNIA": "CA",
    }

    for source in sources:
        with open(source) as file:
            source_data = [line.rstrip() for line in file]
        station_dict = {"callsign": None, "location": None, "frequencies": [], "transmissions": [], "map_areas": []}
        frequencies_list = []
        transmissions_list = []

        # First line of file is the location
        location_line = source_data.pop(0)
        city, state, country = location_line.split(", ")
        station_dict["location"] = f"{city.title()}, {states[state]}"

        while not source_data[0].startswith("CALL SIGN"):
            source_data.pop(0)
        # discard the header
        source_data.pop(0)
        while True:
            frequency_line = source_data.pop(0)
            frequency = {"value": None}
            match = re.search(frequency_pattern, frequency_line)
            if not match:
                break
            callsign = match.group(1)
            if callsign != "" and station_dict["callsign"] is None:
                station_dict["callsign"] = callsign
            value = match.group(2)
            frequency["value"] = number_from_string(value)
            # no comma-separated ranges at present
            times = match.group(3)
            if times != "ALL BROADCAST TIMES":
                time_match = re.match(times_pattern, times)
                frequency["times"] = [{"start": time_match.group(1), "end": time_match.group(2)}]
            frequency["emissions"] = [match.group(4)]
            power = match.group(5)
            frequency["power"] = number_from_string(power)
            station_dict["frequencies"].append(frequency)

        # transmission table header is inconsistent
        # there are one- and two- line variants
        # whitespace is also problematic
        while not source_data[0].startswith("0"):
            source_data.pop(0)
        while True:
            transmission_line = source_data.pop(0)
            if transmission_line == "":
                break
            transmission = {"title": None, "times": None}
            # there are multiple patterns for transmissions:
            match = re.search(transmission_data_pattern, transmission_line)
            if not match:
                match = re.search(transmission_test_pattern, transmission_line)
            times = [time for time in [match.group(1), match.group(2)] if time != "----"]
            transmission["times"] = [{"initial": time} for time in times]
            title = match.group(3)
            valid = None
            map_area = None
            try:
                valid = match.group(4)
                match valid:
                    case None:
                        valid = None
                    case "LATEST":
                        valid = None
                    case _ if "/" in valid:
                        hours, minutes = valid.split("/")
                        valid = [f"{int(hours):02d}00", f"{int(minutes):02d}00"]
                    case _:
                        valid = [f"{valid:0>4}"]
                if valid is not None:
                    for index in range(len(times)):
                        transmission["times"][index]["valid"] = valid[index]
                map_area = match.group(5)
                transmission["map_area"] = map_area
            except IndexError:
                pass
            transmission["title"] = re.sub(r"\s*\d{3}/\d{3}$", "", title.title())
            station_dict["transmissions"].append(transmission)

        # map areas tables also problematic
        while not source_data[0].startswith("MAP"):
            source_data.pop(0)
        while True:
            map_area_line = source_data.pop(0)
            if map_area_line == "":
                break
            match = re.search(map_area_most_pattern, map_area_line)
            if match:
                station_dict["map_areas"].append({"ident": match.group(1), "description": match.group(2)})
                station_dict["map_areas"].append({"ident": match.group(3), "description": match.group(4)})
            else:
                match = re.search(map_area_gulf_pattern, map_area_line)
                if match:
                    station_dict["map_areas"].append({"ident": match.group(1), "description": match.group(2)})

        while True:
            date_line = source_data.pop(0)
            date_pattern = re.compile(r"Information dated (.*)\)")
            match = re.search(date_pattern, date_line)
            if match:
                this_date = datetime.strptime(match.group(1), "%B %d, %Y").date()
                if latest_date < this_date:
                    latest_date = this_date
                break
        schedule_dict["stations"].append(station_dict)

    schedule_dict["date"] = latest_date.strftime(date_format)
    print(json.dumps(schedule_dict))
