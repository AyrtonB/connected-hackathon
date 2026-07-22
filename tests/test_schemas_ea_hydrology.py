from datetime import datetime

from wxdecide.schemas.ea_hydrology import Measure, Reading, Station


def test_station_flattens_jsonld_id_references():
    raw = {
        "@id": "http://environment.data.gov.uk/hydrology/id/stations/abc123",
        "label": "Evesham",
        "riverName": "River Avon",
        "lat": 51.6,
        "long": -0.08,
        "type": [
            {"@id": "http://environment.data.gov.uk/reference/def/core/SamplingLocation"},
            {"@id": "http://environment.data.gov.uk/flood-monitoring/def/core/RainfallStation"},
        ],
        "status": [{"@id": "http://environment.data.gov.uk/flood-monitoring/def/core/statusActive"}],
        "measures": [
            {"@id": "http://environment.data.gov.uk/hydrology/id/measures/abc123-rainfall-t-900-mm-qualified"}
        ],
    }

    station = Station.model_validate(raw)

    assert station.id == "http://environment.data.gov.uk/hydrology/id/stations/abc123"
    assert station.label == "Evesham"
    assert station.river_name == "River Avon"
    assert station.lat == 51.6
    assert station.types == [
        "http://environment.data.gov.uk/reference/def/core/SamplingLocation",
        "http://environment.data.gov.uk/flood-monitoring/def/core/RainfallStation",
    ]
    assert station.statuses == ["http://environment.data.gov.uk/flood-monitoring/def/core/statusActive"]
    assert station.measure_ids == [
        "http://environment.data.gov.uk/hydrology/id/measures/abc123-rainfall-t-900-mm-qualified"
    ]


def test_station_defaults_missing_lists_to_empty():
    station = Station.model_validate({"@id": "http://example.org/stations/1"})

    assert station.types == []
    assert station.statuses == []
    assert station.measure_ids == []


def test_reading_flattens_measure_reference():
    raw = {
        "measure": {
            "@id": "http://environment.data.gov.uk/hydrology/id/measures/abc123-temp-m-86400-C-qualified"
        },
        "date": "2025-10-02",
        "dateTime": "2025-10-02T00:00:00",
        "value": 13.227,
        "quality": "Unchecked",
    }

    reading = Reading.model_validate(raw)

    assert reading.measure_id == (
        "http://environment.data.gov.uk/hydrology/id/measures/abc123-temp-m-86400-C-qualified"
    )
    assert reading.date_time == datetime(2025, 10, 2)
    assert reading.value == 13.227
    assert reading.quality == "Unchecked"


def test_measure_flattens_station_reference():
    raw = {
        "@id": "http://environment.data.gov.uk/hydrology/id/measures/abc123-temp-m-86400-C-qualified",
        "label": "Daily mean Temperature (°C) time series for Evesham",
        "parameter": "TEMPERATURE",
        "parameterName": "Temperature",
        "period": 86400,
        "periodName": "daily",
        "valueType": "mean",
        "unitName": "°C",
        "station": {"@id": "http://environment.data.gov.uk/hydrology/id/stations/abc123"},
    }

    measure = Measure.model_validate(raw)

    assert measure.parameter == "TEMPERATURE"
    assert measure.period == 86400
    assert measure.period_name == "daily"
    assert measure.value_type == "mean"
    assert measure.unit_name == "°C"
    assert measure.station_id == "http://environment.data.gov.uk/hydrology/id/stations/abc123"


def test_measure_station_id_defaults_to_none():
    measure = Measure.model_validate(
        {
            "@id": "http://environment.data.gov.uk/hydrology/id/measures/abc123-temp-m-86400-C-qualified",
            "parameter": "TEMPERATURE",
            "period": 86400,
        }
    )

    assert measure.station_id is None
