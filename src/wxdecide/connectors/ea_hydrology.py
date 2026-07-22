"""Client for the Environment Agency Hydrology API.

Docs: https://environment.data.gov.uk/hydrology/doc/reference

Unlike the UKPN Explore API, this is a linked-data API with no total count or "next page" link
in its responses. List endpoints such as `/id/stations` and `/id/measures/{id}/readings` are
paged purely via `_limit`/`_offset`, so the only reliable end-of-data signal is a page coming
back shorter than requested.
"""

from __future__ import annotations

import time
from typing import Any, Self, TypeVar

import httpx
from pydantic import BaseModel

from wxdecide.schemas.ea_hydrology import Measure, Reading, Station

BASE_URL = "https://environment.data.gov.uk/hydrology"

DEFAULT_PAGE_SIZE = 2000

MAX_RETRIES = 5
RETRY_BACKOFF_SECONDS = 2.0

# Station type marking a flow/level gauge that also carries a temperature sensor. Filtering
# `/id/stations` by this type (or by `observedProperty=temperature`) is what the Hydrology
# Data Explorer UI's "stations with temperature data" toggle does under the hood.
WITH_TEMPERATURE_TYPE = "http://environment.data.gov.uk/flood-monitoring/def/core/WithTemperature"

# Station type marking an actual river-flow gauge, as opposed to the much larger set of
# EA stations measuring level only, water quality, rainfall, or groundwater — those other
# types are never National River Flow Archive (NRFA) members, so filtering to this type first
# is what makes a `nrfa_station_id` match worth expecting (see `wxdecide.geo` and
# `wxdecide.connectors.catchment_boundaries`).
RIVER_FLOW_TYPE = "http://environment.data.gov.uk/flood-monitoring/def/core/RiverFlow"

ModelT = TypeVar("ModelT", bound=BaseModel)


class EAHydrologyClient:
    """Thin client over the Environment Agency's Hydrology API."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        retry_backoff_seconds: float = RETRY_BACKOFF_SECONDS,
    ) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)
        self._retry_backoff_seconds = retry_backoff_seconds

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get_stations(
        self,
        *,
        params: dict[str, Any] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[Station]:
        """Fetch every station matching `params`, transparently following pagination.

        `params` accepts any query parameters documented for `/id/stations`, e.g.
        `{"status": ["statusActive", "statusSuspended"], "type": WITH_TEMPERATURE_TYPE,
        "_projection": "lat,long,type,status,measures(qualifier)"}`. List values are sent as
        repeated query keys (as the API expects for multi-valued filters like `status`).
        """
        return self._get_all_pages("/id/stations", Station, params=params, page_size=page_size)

    def get_readings(
        self,
        measure_id: str,
        *,
        params: dict[str, Any] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[Reading]:
        """Fetch every reading for a measure (time series), transparently following pagination.

        `measure_id` may be a full measure URI (as found in `Station.measure_ids`) or just its
        notation. `params` accepts any query parameters documented for `/readings`, e.g.
        `{"min-date": "2025-10-01", "max-date": "2025-11-21"}`, or `{"latest": ""}` for just the
        most recent value.
        """
        notation = measure_id.rsplit("/", 1)[-1]
        path = f"/id/measures/{notation}/readings"
        return self._get_all_pages(path, Reading, params=params, page_size=page_size)

    def get_measure(self, measure_id: str) -> Measure:
        """Fetch a single measure's own metadata (parameter, period, statistic, unit, station).

        `measure_id` may be a full measure URI (as found in `Station.measure_ids`) or just its
        notation.
        """
        notation = measure_id.rsplit("/", 1)[-1]
        response = self._get(f"/id/measures/{notation}")
        return Measure.model_validate(response.json()["items"][0])

    def _get_all_pages(
        self,
        path: str,
        model: type[ModelT],
        *,
        params: dict[str, Any] | None,
        page_size: int,
    ) -> list[ModelT]:
        items: list[ModelT] = []
        offset = 0
        while True:
            page = self._get_page(path, model, params=params, limit=page_size, offset=offset)
            items.extend(page)
            if len(page) < page_size:
                break
            offset += page_size
        return items

    def _get_page(
        self,
        path: str,
        model: type[ModelT],
        *,
        params: dict[str, Any] | None,
        limit: int,
        offset: int,
    ) -> list[ModelT]:
        query: dict[str, Any] = dict(params or {})
        query["_limit"] = limit
        query["_offset"] = offset
        response = self._get(path, query)
        return [model.model_validate(item) for item in response.json()["items"]]

    def _get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """GET with retry-with-backoff on 429/403s.

        429 (Too Many Requests) is the API's documented rate-limit response under sustained use.
        403 (Forbidden) isn't documented as retryable, but has been observed to be a transient
        blip too — an identical request retried by hand immediately after a 403 returned 200 —
        rather than a sustained block, so it's treated the same way here.
        """
        response = self._client.get(path, params=params)
        for attempt in range(MAX_RETRIES):
            if response.status_code not in (429, 403):
                break
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else self._retry_backoff_seconds * (2**attempt)
            time.sleep(wait)
            response = self._client.get(path, params=params)
        response.raise_for_status()
        return response
