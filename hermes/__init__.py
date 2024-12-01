import json
import os
from contextlib import suppress

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError

from hermes.extensions import db
from hermes.models import Frequency, MapArea, Schedule, Station, TimeList, TimeRange, Transmission
from hermes.schemas import frequency as frequency_schema
from hermes.schemas import map_area as map_area_schema
from hermes.schemas import schedule as schedule_schema
from hermes.schemas import station as station_schema
from hermes.schemas import transmission as transmission_schema


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.from_object("hermes.config.Config")
    else:
        app.config.from_mapping(test_config)

    # make sure instance path exists
    with suppress(OSError):
        os.makedirs(app.instance_path)

    # init extensions
    db.init_app(app)

    # add commands
    from hermes.commands import init_db, load_schedule, make_arrl_schedule, make_wefax_schedule

    app.cli.add_command(init_db)
    app.cli.add_command(load_schedule)
    app.cli.add_command(make_arrl_schedule)
    app.cli.add_command(make_wefax_schedule)

    # now routes
    from hermes.routes import main_bp

    app.register_blueprint(main_bp)
    from hermes.routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    return app
