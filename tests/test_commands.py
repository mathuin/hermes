import json

from radio_browser import create_app
from radio_browser.extensions import db
from radio_browser.schemas import schedule as schedule_schema


def test_init_db_command(runner, app):
    with app.app_context():
        result = runner.invoke(args=["init-db", "--drop"])
        assert result.exit_code == 0
        assert "Dropped all tables." in result.output
        result = runner.invoke(args=["init-db"])
        assert result.exit_code == 0
        assert "Database initialized successfully!" in result.output


def test_load_schedule_command(
    runner, app, fs, schedule, station, frequency, timerange, transmission, timelist, map_area
):
    file_path = "composite.json"
    fs.create_file(file_path, contents=json.dumps(schedule_schema.dump(schedule)))
    with app.app_context():
        try:
            result = runner.invoke(args=["load-schedule", file_path])
        except IntegrityError as exc:
            raise IntegrityError(f"IntegrityError {exc}") from None
    with app.app_context():
        result = runner.invoke(args=["init-db", "--drop"])
        assert result.exit_code == 0
    with app.app_context():
        result = runner.invoke(args=["load-schedule", file_path])
        assert result.exit_code == 0
        assert "Schedule 'Test Schedule' loaded successfully." in result.output


from pathlib import Path


def test_make_arrl_schedule(runner):
    data_path = Path(__file__).resolve().parent / "test_commands"
    bulletin_path = data_path / "arlb006.txt"
    schedule_path = data_path / "arrl.json"
    with open(schedule_path) as file:
        expected_output = file.read()
    result = runner.invoke(args=["make-arrl-schedule", str(bulletin_path)])
    assert result.exit_code == 0, result.output
    assert result.output == expected_output


def test_make_wefax_schedule(runner):
    data_path = Path(__file__).resolve().parent / "test_commands"
    schedule_path = data_path / "wefax.json"
    tags = ["ak", "gulf", "hi", "marsh", "reyes"]
    data_files = [str(data_path / f"hf{tag}.txt") for tag in tags]
    with open(schedule_path) as file:
        expected_output = file.read()
    result = runner.invoke(args=["make-wefax-schedule", *data_files])
    assert result.exit_code == 0, result.output
    assert result.output == expected_output
