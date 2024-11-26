from datetime import datetime, time

from flask import Blueprint, abort, jsonify, render_template, request
from marshmallow import ValidationError
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import aliased

from radio_browser.enum import DayOfWeek
from radio_browser.extensions import db, time_format
from radio_browser.filter import DateTimeRange, Event, get_events
from radio_browser.models import Frequency, MapArea, Schedule, Station, Transmission
from radio_browser.schemas import frequencies as frequencies_schema
from radio_browser.schemas import frequency as frequency_schema
from radio_browser.schemas import map_area as map_area_schema
from radio_browser.schemas import map_areas as map_areas_schema
from radio_browser.schemas import schedule as schedule_schema
from radio_browser.schemas import schedules as schedules_schema
from radio_browser.schemas import station as station_schema
from radio_browser.schemas import stations as stations_schema
from radio_browser.schemas import transmission as transmission_schema
from radio_browser.schemas import transmissions as transmissions_schema

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    schedules = Schedule.query.order_by(Schedule.name).all()
    return render_template("index.html", schedules=schedules)


@main_bp.route("/stations/<int:schedule_id>")
def get_stations_by_schedule(schedule_id):
    stations = Station.query.filter_by(schedule_id=schedule_id).all()
    return jsonify(
        [{"id": station.id, "callsign": station.callsign, "location": station.location} for station in stations]
    )


@main_bp.route("/filter", methods=["POST"])
def filter_schedule():
    json_data = request.get_json()
    required_keys = ["start_day", "start_time", "end_time", "station_ids"]
    missing_keys = [key for key in required_keys if key not in json_data]
    start_day = DayOfWeek[json_data["start_day"]]
    start_time = datetime.strptime(json_data["start_time"], time_format).time()
    end_time = datetime.strptime(json_data["end_time"], time_format).time()

    dtr = DateTimeRange(day=start_day, start_time=start_time, end_time=end_time)
    stations = Station.query.filter(Station.id.in_(json_data["station_ids"])).all()

    events = get_events(dtr, stations)
    return jsonify(
        [
            {
                "day": event.day.value,
                "time": event.time.strftime(time_format),
                "name": event.name,
                "station": event.station,
                "frequencies": event.frequencies,
            }
            for event in events
        ]
    )


api_bp = Blueprint("api", __name__)


@api_bp.route("/schedules")
def get_schedules():
    subquery = (
        db.session.query(Schedule.name, func.max(Schedule.date).label("max_date")).group_by(Schedule.name).subquery()
    )

    latest_schedules = (
        db.session.query(Schedule)
        .join(subquery, (Schedule.name == subquery.c.name) & (Schedule.date == subquery.c.max_date))
        .order_by(Schedule.name)
        .all()
    )
    return jsonify(schedules_schema.dump(latest_schedules))


@api_bp.route("/schedules/<int:pk>")
def get_schedule(pk):
    try:
        schedule = Schedule.query.filter(Schedule.id == pk).one()
    except NoResultFound:
        abort(404, "Schedule could not be found")
    schedule_result = schedule_schema.dump(schedule)
    return schedule_result


@api_bp.route("/schedules", methods=["POST"])
def post_schedule():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Missing request data")
    try:
        schedule_data = schedule_schema.load(json_data)
    except ValidationError as err:
        return err.messages, 422
    exists = Schedule.query.filter_by(name=schedule_data["name"], date=schedule_data["date"]).first()
    if exists is not None:
        abort(409, "Schedule with that name and date already exists")
    schedule = Schedule(
        name=schedule_data["name"], date=schedule_data["date"], source_url=schedule_data.get("source_url", None)
    )
    try:
        db.session.add(schedule)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    result = schedule_schema.dump(db.session.get(Schedule, schedule.id))
    return result, 201


@api_bp.route("/schedules/<int:pk>", methods=["DELETE"])
def delete_schedule(pk):
    try:
        schedule = Schedule.query.filter(Schedule.id == pk).one()
    except NoResultFound:
        abort(404, "Schedule could not be found")
    try:
        db.session.delete(schedule)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    return "No content", 204


@api_bp.route("/stations")
def get_stations():
    all_stations = Station.query.all()
    return jsonify(stations_schema.dump(all_stations))


@api_bp.route("/stations/<int:pk>")
def get_station(pk):
    try:
        station = Station.query.filter(Station.id == pk).one()
    except NoResultFound:
        abort(404, "Station could not be found")
    station_result = station_schema.dump(station)
    return station_result


@api_bp.route("/stations", methods=["POST"])
def post_station():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Missing request data")
    try:
        station_data = station_schema.load(json_data)
    except ValidationError as err:
        return err.messages, 422
    try:
        schedule = Schedule.query.filter_by(id=station_data["schedule_id"]).one()
    except NoResultFound:
        abort(404, "Schedule could not be found")
    exists = Station.query.filter_by(
        schedule_id=station_data["schedule_id"], callsign=station_data["callsign"], location=station_data["location"]
    ).first()
    if exists is not None:
        abort(409, "Station with that callsign and location already exists")
    station = Station(
        schedule=schedule,
        callsign=station_data["callsign"],
        location=station_data["location"],
        region=station_data.get("region", None),
        emissions=station_data.get("emissions", None),
    )
    try:
        schedule.stations.append(station)
        db.session.add(schedule)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    result = station_schema.dump(db.session.get(Station, station.id))
    return result, 201


@api_bp.route("/stations/<int:pk>", methods=["DELETE"])
def delete_station(pk):
    try:
        station = Station.query.filter(Station.id == pk).one()
    except NoResultFound:
        abort(404, "Station could not be found")
    try:
        schedule = Schedule.query.filter(Schedule.id == station.schedule_id).one()
        schedule.stations.remove(station)
        db.session.delete(station)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    return "No content", 204


@api_bp.route("/frequencies")
def get_frequencies():
    all_frequencies = Frequency.query.all()
    return jsonify(frequencies_schema.dump(all_frequencies))


@api_bp.route("/frequencies/<int:pk>")
def get_frequency(pk):
    try:
        frequency = Frequency.query.filter(Frequency.id == pk).one()
    except NoResultFound:
        abort(404, "Frequency could not be found")
    frequency_result = frequency_schema.dump(frequency)
    return frequency_result


@api_bp.route("/frequencies", methods=["POST"])
def post_frequency():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Missing request data")
    try:
        frequency_data = frequency_schema.load(json_data)
    except ValidationError as err:
        return err.messages, 422
    try:
        station = Station.query.filter_by(id=frequency_data["station_id"]).one()
    except NoResultFound:
        abort(404, "Station could not be found")
    exists = Frequency.query.filter_by(station_id=frequency_data["station_id"], value=frequency_data["value"]).first()
    if exists is not None:
        abort(409, "Frequency with that value already exists")
    frequency = Frequency(
        station=station,
        value=frequency_data["value"],
        callsign=frequency_data.get("callsign", None),
        emissions=frequency_data.get("emissions", None),
        times=frequency_data.get("times", None),
        power=frequency_data.get("power", None),
    )
    try:
        station.frequencies.append(frequency)
        db.session.add(station)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    result = frequency_schema.dump(db.session.get(Frequency, frequency.id))
    return result, 201


@api_bp.route("/frequencies/<int:pk>", methods=["DELETE"])
def delete_frequency(pk):
    try:
        frequency = Frequency.query.filter(Frequency.id == pk).one()
    except NoResultFound:
        abort(404, "Frequency could not be found")
    try:
        station = Station.query.filter(Station.id == frequency.station_id).one()
        station.frequencies.remove(frequency)
        db.session.delete(frequency)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    return "No content", 204


@api_bp.route("/transmissions")
def get_transmissions():
    all_transmissions = Transmission.query.all()
    return jsonify(transmissions_schema.dump(all_transmissions))


@api_bp.route("/transmissions/<int:pk>")
def get_transmission(pk):
    try:
        transmission = Transmission.query.filter(Transmission.id == pk).one()
    except NoResultFound:
        abort(404, "Transmission could not be found")
    transmission_result = transmission_schema.dump(transmission)
    return transmission_result


@api_bp.route("/transmissions", methods=["POST"])
def post_transmission():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Missing request data")
    try:
        transmission_data = transmission_schema.load(json_data)
    except ValidationError as err:
        return err.messages, 422
    try:
        station = Station.query.filter_by(id=transmission_data["station_id"]).one()
    except NoResultFound:
        abort(404, "Station could not be found")
    if "map_area_id" in transmission_data and transmission_data["map_area_id"] is not None:
        try:
            map_area = MapArea.query.filter_by(id=transmission_data["map_area_id"]).one()
        except NoResultFound:
            abort(404, "Map area could not be found")
    else:
        map_area = None
    exists = Transmission.query.filter_by(
        station_id=transmission_data["station_id"], title=transmission_data["title"]
    ).first()
    if exists is not None:
        abort(409, "Transmission with that title already exists")
    transmission = Transmission(
        station=station,
        title=transmission_data["title"],
        times=transmission_data.get("times", None),
        emissions=transmission_data.get("emissions", None),
        days=transmission_data.get("days", None),
        map_area=map_area,
    )
    try:
        station.transmissions.append(transmission)
        db.session.add(station)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    result = transmission_schema.dump(db.session.get(Transmission, transmission.id))
    return result, 201


@api_bp.route("/transmissions/<int:pk>", methods=["DELETE"])
def delete_transmission(pk):
    try:
        transmission = Transmission.query.filter(Transmission.id == pk).one()
    except NoResultFound:
        abort(404, "Transmission could not be found")
    try:
        station = Station.query.filter(Station.id == transmission.station_id).one()
        station.transmissions.remove(transmission)
        db.session.delete(transmission)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    return "No content", 204


@api_bp.route("/map_areas")
def get_map_areas():
    all_map_areas = MapArea.query.all()
    return jsonify(map_areas_schema.dump(all_map_areas))


@api_bp.route("/map_areas/<int:pk>")
def get_map_area(pk):
    try:
        map_area = MapArea.query.filter(MapArea.id == pk).one()
    except NoResultFound:
        abort(404, "Map area could not be found")
    map_area_result = map_area_schema.dump(map_area)
    return map_area_result


@api_bp.route("/map_areas", methods=["POST"])
def post_map_area():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Missing request data")
    try:
        map_area_data = map_area_schema.load(json_data)
    except ValidationError as err:
        return err.messages, 422
    try:
        station = Station.query.filter_by(id=map_area_data["station_id"]).one()
    except NoResultFound:
        abort(404, "Station could not be found")
    exists = MapArea.query.filter_by(station_id=map_area_data["station_id"], ident=map_area_data["ident"]).first()
    if exists is not None:
        abort(409, "Map area with that ident already exists")
    map_area = MapArea(
        station=station,
        ident=map_area_data["ident"],
        description=map_area_data["description"],
    )
    try:
        station.map_areas.append(map_area)
        db.session.add(station)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    result = map_area_schema.dump(db.session.get(MapArea, map_area.id))
    return result, 201


@api_bp.route("/map_areas/<int:pk>", methods=["DELETE"])
def delete_map_area(pk):
    try:
        map_area = MapArea.query.filter(MapArea.id == pk).one()
    except NoResultFound:
        abort(404, "Map area could not be found")
    still_in_use = Transmission.query.filter(Transmission.map_area_id == pk).first()
    if still_in_use is not None:
        abort(403, "Map area still in use")
    try:
        station = Station.query.filter(Station.id == map_area.station_id).one()
        station.map_areas.remove(map_area)
        db.session.delete(map_area)
        db.session.commit()
    except Exception as e:  # pragma: no cover
        abort(400, description=str(e))
    return "No content", 204
