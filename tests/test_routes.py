import json


def test_index(client, schedule, station, frequency, transmission):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Schedules:" in response.data
    assert b"Test Schedule" in response.data
    assert b"Stations:" in response.data
    assert b"Filter Schedule" in response.data


def test_get_stations_by_schedule(client, schedule, station):
    response = client.get("/stations/1")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    assert json_data[0]["callsign"] == "Test Station"


def test_filter_schedule(client, schedule, station, frequency, transmission, timelist):
    post_data = {"start_day": "Mon", "start_time": "0000", "end_time": "0100", "station_ids": [1]}
    response = client.post("/filter", json=post_data)
    assert response.status_code == 200
    response_data = response.get_json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1


def test_get_schedules(client, schedule):
    response = client.get("/api/schedules")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    assert json_data[0]["name"] == "Test Schedule"


def test_get_schedule(client, schedule):
    response = client.get("/api/schedules/1")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, dict)
    assert json_data["name"] == "Test Schedule"
    response = client.get("/api/schedules/2")
    assert response.status_code == 404


def test_post_schedule(client, schedule):
    response = client.post("/api/schedules", json={})
    assert response.status_code == 400
    assert b"Missing request data" in response.data
    response = client.post("/api/schedules", json={"name": "New Schedule", "date": "2024-11-21"})
    assert response.status_code == 201, response.data
    data = json.loads(response.data)
    assert data["date"] == "2024-11-21"
    response = client.post("/api/schedules", json={"name": "New Schedule", "date": "2024-11-21"})
    assert response.status_code == 409, response.data
    assert b"Schedule with that name and date already exists" in response.data
    response = client.post("/api/schedules", json={"name": "", "date": ""})
    assert response.status_code == 422, response.data


def test_delete_schedule(client, schedule):
    response = client.delete("/api/schedules/1")
    assert response.status_code == 204
    response = client.delete("/api/schedules/1")
    assert response.status_code == 404


def test_get_stations(client, schedule, station):
    response = client.get("/api/stations")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    assert json_data[0]["callsign"] == "Test Station"


def test_get_station(client, schedule, station):
    response = client.get("/api/stations/1")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, dict)
    assert json_data["callsign"] == "Test Station"
    response = client.get("/api/stations/2")
    assert response.status_code == 404


def test_post_station(client, schedule, station):
    response = client.post("/api/stations", json={})
    assert response.status_code == 400
    assert b"Missing request data" in response.data
    response = client.post(
        "/api/stations", json={"schedule_id": 1, "callsign": "New Station", "location": "New Location"}
    )
    assert response.status_code == 201, response.data
    data = json.loads(response.data)
    assert data["location"] == "New Location"
    response = client.post(
        "/api/stations", json={"schedule_id": 1, "callsign": "New Station", "location": "New Location"}
    )
    assert response.status_code == 409, response.data
    assert b"Station with that callsign and location already exists" in response.data
    response = client.post(
        "/api/stations", json={"schedule_id": 3, "callsign": "New Station", "location": "New Location"}
    )
    assert response.status_code == 404, response.data
    assert b"Schedule could not be found" in response.data
    response = client.post("/api/stations", json={"name": "", "date": ""})
    assert response.status_code == 422, response.data


def test_delete_station(client, schedule, station):
    response = client.delete("/api/stations/1")
    assert response.status_code == 204
    response = client.delete("/api/stations/1")
    assert response.status_code == 404


def test_get_frequencies(client, schedule, station, frequency):
    response = client.get("/api/frequencies")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    assert json_data[0]["value"] == 123.4


def test_get_frequency(client, schedule, station, frequency):
    response = client.get("/api/frequencies/1")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, dict)
    assert json_data["value"] == 123.4
    response = client.get("/api/frequencies/2")
    assert response.status_code == 404


def test_post_frequency(client, schedule, station, frequency):
    response = client.post("/api/frequencies", json={})
    assert response.status_code == 400
    assert b"Missing request data" in response.data
    response = client.post("/api/frequencies", json={"station_id": 1, "value": 1234.5})
    assert response.status_code == 201, response.data
    data = json.loads(response.data)
    assert data["value"] == 1234.5
    response = client.post("/api/frequencies", json={"station_id": 1, "value": 1234.5})
    assert response.status_code == 409, response.data
    assert b"Frequency with that value already exists" in response.data
    response = client.post("/api/frequencies", json={"station_id": 3, "value": 1234.5})
    assert response.status_code == 404, response.data
    assert b"Station could not be found" in response.data
    response = client.post("/api/frequencies", json={"value": ""})
    assert response.status_code == 422, response.data


def test_delete_frequency(client, schedule, station, frequency):
    response = client.delete("/api/frequencies/1")
    assert response.status_code == 204
    response = client.delete("/api/frequencies/1")
    assert response.status_code == 404


def test_get_transmissions(client, schedule, station, transmission):
    response = client.get("/api/transmissions")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    assert json_data[0]["title"] == "Test Title"


def test_get_transmission(client, schedule, station, transmission, timelist):
    response = client.get("/api/transmissions/1")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, dict)
    assert json_data["title"] == "Test Title"
    assert json_data["times"] == [{"initial": "0030", "rebroadcast": "1230", "transmission_id": 1, "valid": "0000"}]
    response = client.get("/api/transmissions/2")
    assert response.status_code == 404


def test_post_transmission(client, schedule, station, transmission, map_area):
    response = client.post("/api/transmissions", json={})
    assert response.status_code == 400
    assert b"Missing request data" in response.data
    response = client.post("/api/transmissions", json={"station_id": 1, "title": "Again", "map_area_id": 2})
    assert response.status_code == 404, response.data
    assert b"Map area could not be found" in response.data
    response = client.post("/api/transmissions", json={"station_id": 1, "title": "Again", "map_area_id": 1})
    assert response.status_code == 201, response.data
    data = json.loads(response.data)
    assert data["title"] == "Again"
    response = client.post("/api/transmissions", json={"station_id": 1, "title": "Again"})
    assert response.status_code == 409, response.data
    assert b"Transmission with that title already exists" in response.data
    response = client.post("/api/transmissions", json={"station_id": 3, "title": "Again"})
    assert response.status_code == 404, response.data
    assert b"Station could not be found" in response.data
    response = client.post("/api/transmissions", json={"title": ""})
    assert response.status_code == 422, response.data


def test_delete_transmission(client, schedule, station, transmission):
    response = client.delete("/api/transmissions/1")
    assert response.status_code == 204
    response = client.delete("/api/transmissions/1")
    assert response.status_code == 404


def test_get_map_areas(client, schedule, station, map_area):
    response = client.get("/api/map_areas")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    assert json_data[0]["ident"] == "ID"


def test_get_map_area(client, schedule, station, map_area):
    response = client.get("/api/map_areas/1")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, dict)
    assert json_data["ident"] == "ID"
    response = client.get("/api/map_areas/2")
    assert response.status_code == 404


def test_post_map_area(client, schedule, station, map_area):
    response = client.post("/api/map_areas", json={})
    assert response.status_code == 400
    assert b"Missing request data" in response.data
    response = client.post("/api/map_areas", json={"station_id": 1, "ident": "2", "description": "Second"})
    assert response.status_code == 201, response.data
    data = json.loads(response.data)
    assert data["ident"] == "2"
    response = client.post("/api/map_areas", json={"station_id": 1, "ident": "2", "description": "Second"})
    assert response.status_code == 409, response.data
    assert b"Map area with that ident already exists" in response.data
    response = client.post("/api/map_areas", json={"station_id": 3, "ident": "2", "description": "Second"})
    assert response.status_code == 404, response.data
    assert b"Station could not be found" in response.data
    response = client.post("/api/map_areas", json={"ident": ""})
    assert response.status_code == 422, response.data


def test_delete_map_area(client, schedule, station, transmission, map_area):
    response = client.delete("/api/map_areas/1")
    assert response.status_code == 403, response.data
    assert b"Map area still in use" in response.data
    response = client.delete("/api/transmissions/1")
    assert response.status_code == 204, response.data
    response = client.delete("/api/map_areas/1")
    assert response.status_code == 204, response.data
    response = client.delete("/api/map_areas/1")
    assert response.status_code == 404, response.data
