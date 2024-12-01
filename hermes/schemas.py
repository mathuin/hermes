from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemySchema

from hermes import enum, models
from hermes.extensions import date_format, time_format


class Schema(SQLAlchemySchema):
    class Meta:
        load_instance = True


class TimeRange(Schema):
    class Meta:
        model = models.TimeRange

    frequency_id = fields.Integer(required=True)
    start = fields.Time(time_format)
    end = fields.Time(time_format)


timerange = TimeRange()
timeranges = TimeRange(many=True)


class Frequency(Schema):
    class Meta:
        model = models.Frequency

    station_id = fields.Integer(required=True)
    value = fields.Float(required=True)
    callsign = fields.String()
    emissions = fields.List(fields.Enum(enum.EmissionType))
    times = fields.Nested(TimeRange, many=True)
    power = fields.Float()


frequency = Frequency()
frequencies = Frequency(many=True)


class TimeList(Schema):
    class Meta:
        model = models.TimeList

    transmission_id = fields.Integer(required=True)
    initial = fields.Time(time_format, required=True)
    rebroadcast = fields.Time(time_format)
    valid = fields.Time(time_format)


timelist = TimeList()
timelists = TimeList(many=True)


class Transmission(Schema):
    class Meta:
        model = models.Transmission

    station_id = fields.Integer(required=True)
    title = fields.String(required=True)
    times = fields.Nested(TimeList, many=True)
    emissions = fields.List(fields.Enum(enum.EmissionType))
    days = fields.List(fields.Enum(enum.DayOfWeek))
    map_area_id = fields.Integer()


transmission = Transmission()
transmissions = Transmission(many=True)


class MapArea(Schema):
    class Meta:
        model = models.MapArea

    station_id = fields.Integer(required=True)
    ident = fields.String(required=True)
    description = fields.String(required=True)


map_area = MapArea()
map_areas = MapArea(many=True)


class Station(Schema):
    class Meta:
        model = models.Station

    schedule_id = fields.Integer(required=True)
    callsign = fields.String(required=True)
    location = fields.String(required=True)
    region = fields.String()
    emissions = fields.List(fields.Enum(enum.EmissionType))

    frequencies = fields.Nested(Frequency, many=True)
    transmissions = fields.Nested(Transmission, many=True)
    map_areas = fields.Nested(MapArea, many=True)


station = Station()
stations = Station(many=True)


class Schedule(Schema):
    class Meta:
        model = models.Schedule

    name = fields.String(required=True)
    date = fields.Date(date_format, required=True)
    source_url = fields.URL()

    stations = fields.Nested(Station, many=True)


schedule = Schedule()
schedules = Schedule(many=True)
