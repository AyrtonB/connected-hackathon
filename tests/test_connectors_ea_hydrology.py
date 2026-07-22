from urllib.parse import parse_qs

import httpx

from wxdecide.connectors.ea_hydrology import EAHydrologyClient


def _station(n: int) -> dict:
    return {"@id": f"http://environment.data.gov.uk/hydrology/id/stations/{n}", "lat": 51.0 + n}


def _paged_transport(all_items: list[dict]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/hydrology/id/stations"
        query = parse_qs(request.url.query.decode())
        limit = int(query["_limit"][0])
        offset = int(query["_offset"][0])
        page = all_items[offset : offset + limit]
        return httpx.Response(200, json={"items": page})

    return httpx.MockTransport(handler)


def test_get_stations_returns_single_short_page():
    items = [_station(1), _station(2)]

    with EAHydrologyClient(transport=_paged_transport(items)) as client:
        stations = client.get_stations(page_size=10)

    assert [s.id for s in stations] == [item["@id"] for item in items]


def test_get_stations_follows_pagination_across_multiple_pages():
    items = [_station(n) for n in range(5)]

    with EAHydrologyClient(transport=_paged_transport(items)) as client:
        stations = client.get_stations(page_size=2)

    assert [s.id for s in stations] == [item["@id"] for item in items]


def test_get_stations_forwards_filter_params():
    items = [_station(1)]
    seen_queries: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_queries.append(parse_qs(request.url.query.decode()))
        return httpx.Response(200, json={"items": items})

    with EAHydrologyClient(transport=httpx.MockTransport(handler)) as client:
        client.get_stations(
            params={"status": ["statusActive", "statusSuspended"], "type": "RainfallStation"},
            page_size=10,
        )

    assert seen_queries[0]["status"] == ["statusActive", "statusSuspended"]
    assert seen_queries[0]["type"] == ["RainfallStation"]


def _reading(n: int) -> dict:
    return {
        "measure": {"@id": "http://environment.data.gov.uk/hydrology/id/measures/abc-temp-m-86400-C-qualified"},
        "date": f"2025-10-{n:02d}",
        "dateTime": f"2025-10-{n:02d}T00:00:00",
        "value": 10.0 + n,
    }


def test_get_readings_resolves_path_from_full_measure_uri():
    items = [_reading(1), _reading(2)]
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        return httpx.Response(200, json={"items": items})

    with EAHydrologyClient(transport=httpx.MockTransport(handler)) as client:
        readings = client.get_readings(
            "http://environment.data.gov.uk/hydrology/id/measures/abc-temp-m-86400-C-qualified",
            page_size=10,
        )

    assert seen_paths[0] == "/hydrology/id/measures/abc-temp-m-86400-C-qualified/readings"
    assert [r.value for r in readings] == [11.0, 12.0]


def test_get_readings_follows_pagination():
    items = [_reading(n) for n in range(1, 6)]

    def handler(request: httpx.Request) -> httpx.Response:
        query = parse_qs(request.url.query.decode())
        limit = int(query["_limit"][0])
        offset = int(query["_offset"][0])
        return httpx.Response(200, json={"items": items[offset : offset + limit]})

    with EAHydrologyClient(transport=httpx.MockTransport(handler)) as client:
        readings = client.get_readings("abc-temp-m-86400-C-qualified", page_size=2)

    assert len(readings) == 5


def test_get_measure_resolves_path_and_parses_first_item():
    measure = {
        "@id": "http://environment.data.gov.uk/hydrology/id/measures/abc-temp-m-86400-C-qualified",
        "parameter": "TEMPERATURE",
        "parameterName": "Temperature",
        "period": 86400,
        "periodName": "daily",
        "valueType": "mean",
        "unitName": "°C",
        "station": {"@id": "http://environment.data.gov.uk/hydrology/id/stations/abc"},
    }
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        return httpx.Response(200, json={"items": [measure]})

    with EAHydrologyClient(transport=httpx.MockTransport(handler)) as client:
        result = client.get_measure(
            "http://environment.data.gov.uk/hydrology/id/measures/abc-temp-m-86400-C-qualified"
        )

    assert seen_paths[0] == "/hydrology/id/measures/abc-temp-m-86400-C-qualified"
    assert result.parameter == "TEMPERATURE"
    assert result.period == 86400
    assert result.value_type == "mean"
    assert result.station_id == "http://environment.data.gov.uk/hydrology/id/stations/abc"


def test_get_stations_retries_on_429_then_succeeds():
    items = [_station(1)]
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(429)
        return httpx.Response(200, json={"items": items})

    with EAHydrologyClient(
        transport=httpx.MockTransport(handler), retry_backoff_seconds=0.001
    ) as client:
        stations = client.get_stations(page_size=10)

    assert call_count == 3
    assert [s.id for s in stations] == [item["@id"] for item in items]


def test_get_stations_raises_after_exhausting_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    with EAHydrologyClient(
        transport=httpx.MockTransport(handler), retry_backoff_seconds=0.001
    ) as client:
        try:
            client.get_stations(page_size=10)
        except httpx.HTTPStatusError as exc:
            assert exc.response.status_code == 429
        else:
            raise AssertionError("expected HTTPStatusError")


def test_get_stations_retries_on_403_then_succeeds():
    items = [_station(1)]
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return httpx.Response(403)
        return httpx.Response(200, json={"items": items})

    with EAHydrologyClient(
        transport=httpx.MockTransport(handler), retry_backoff_seconds=0.001
    ) as client:
        stations = client.get_stations(page_size=10)

    assert call_count == 2
    assert [s.id for s in stations] == [item["@id"] for item in items]
