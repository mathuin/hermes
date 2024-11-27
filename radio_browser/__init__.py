import json
import os
from contextlib import suppress

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError

from radio_browser.extensions import db
from radio_browser.models import Frequency, MapArea, Schedule, Station, TimeList, TimeRange, Transmission
from radio_browser.schemas import frequency as frequency_schema
from radio_browser.schemas import map_area as map_area_schema
from radio_browser.schemas import schedule as schedule_schema
from radio_browser.schemas import station as station_schema
from radio_browser.schemas import transmission as transmission_schema


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.from_object("radio_browser.config.Config")
    else:
        app.config.from_mapping(test_config)

    # make sure instance path exists
    with suppress(OSError):
        os.makedirs(app.instance_path)

    # init extensions
    db.init_app(app)

    # add commands
    from radio_browser.commands import init_db, load_schedule, make_arrl_schedule, make_wefax_schedule

    app.cli.add_command(init_db)
    app.cli.add_command(load_schedule)
    app.cli.add_command(make_arrl_schedule)
    app.cli.add_command(make_wefax_schedule)

    # now routes
    from radio_browser.routes import main_bp

    app.register_blueprint(main_bp)
    from radio_browser.routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    return app
