"""Pydantic models for the Environment Agency Hydrology API.

This API (environment.data.gov.uk/hydrology) is linked-data flavoured: reference fields come
back as JSON-LD nodes of the form `{"@id": "<uri>"}` rather than plain strings. The model below
flattens those into plain URI strings for convenience.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _as_uri(value: object) -> str:
    return value["@id"] if isinstance(value, dict) else value


class Station(BaseModel):
    """A single monitoring station from the `/hydrology/id/stations` endpoint.

    `types` and `statuses` are the station's type/status URIs (e.g. a `RainfallStation` type,
    or a `statusActive` status). `measure_ids` are URIs identifying each time series available
    at this station (e.g. a 15-minute flow measure) — dereference one via `Measure` to read its
    readings or learn what it actually measures. `river_name` is what lets stations be grouped
    or filtered by river. `nrfa_station_id` is set when this gauge is also a National River Flow
    Archive station — the join key to catchment boundary polygons in
    `wxdecide.schemas.catchment.CatchmentBoundary`.
    """

    id: str = Field(alias="@id")
    label: str | None = None
    river_name: str | None = Field(default=None, alias="riverName")
    lat: float | None = None
    long: float | None = None
    types: list[str] = Field(default_factory=list, alias="type")
    statuses: list[str] = Field(default_factory=list, alias="status")
    measure_ids: list[str] = Field(default_factory=list, alias="measures")
    nrfa_station_id: str | None = Field(default=None, alias="nrfaStationID")

    @field_validator("types", "statuses", "measure_ids", mode="before")
    @classmethod
    def _flatten_uris(cls, value: object) -> list[str]:
        if value is None:
            return []
        return [_as_uri(item) for item in value]

    @field_validator("label", "river_name", mode="before")
    @classmethod
    def _join_name_variants(cls, value: object) -> str | None:
        # Some stations report multiple name variants as a list — bilingual Welsh/English
        # river names (["Afon Tanat", "River Tanat"]) or duplicate casings for a station label
        # (["Beach's Mill", "Beach'S Mill"]).
        if isinstance(value, list):
            return " / ".join(value) if value else None
        return value


class Measure(BaseModel):
    """Metadata describing a single timeseries at a station (as opposed to its readings).

    This is what turns an opaque measure URI into a labelled attribute: `parameter` (e.g.
    TEMPERATURE/FLOW/LEVEL), `period` (in seconds — 86400 for daily, 900 for 15-minute) and
    `value_type` (mean/min/max/instantaneous) together identify what a given timeseries is.
    """

    id: str = Field(alias="@id")
    label: str | None = None
    parameter: str
    parameter_name: str | None = Field(default=None, alias="parameterName")
    period: int
    period_name: str | None = Field(default=None, alias="periodName")
    value_type: str | None = Field(default=None, alias="valueType")
    unit_name: str | None = Field(default=None, alias="unitName")
    station_id: str | None = Field(default=None, alias="station")

    @field_validator("station_id", mode="before")
    @classmethod
    def _flatten_station_uri(cls, value: object) -> str | None:
        return None if value is None else _as_uri(value)


class Reading(BaseModel):
    """A single timestamped value from a measure's `/readings` endpoint.

    `measure_id` identifies which time series this reading belongs to (e.g. a station's daily
    mean temperature series) — join it back to `Station.measure_ids` to know where it's from.
    """

    measure_id: str = Field(alias="measure")
    date_time: datetime = Field(alias="dateTime")
    value: float | None = None
    quality: str | None = None

    @field_validator("measure_id", mode="before")
    @classmethod
    def _flatten_measure_uri(cls, value: object) -> str:
        return _as_uri(value)
