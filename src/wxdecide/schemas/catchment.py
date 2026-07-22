"""Pydantic model for a gauging station's upstream catchment boundary polygon."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CatchmentBoundary(BaseModel):
    """Upstream drainage-area polygon for an NRFA gauging station.

    `nrfa_station_id` is the join key back to `Station.nrfa_station_id` on EA hydrology stations
    that are also NRFA gauges — not every station has a match, since this only covers the ~671
    catchments in the CAMELS-GB set (see `wxdecide.connectors.catchment_boundaries`). `geometry`
    is a GeoJSON Polygon/MultiPolygon in WGS84 (lon/lat), suitable for intersecting against
    precipitation grids.
    """

    nrfa_station_id: str
    area_km2: float
    geometry: dict[str, Any]
