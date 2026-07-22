"""Geospatial helpers for locating hydrology stations relative to river geometries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import Point, shape
from shapely.ops import unary_union

from wxdecide.schemas.catchment import CatchmentBoundary
from wxdecide.schemas.ea_hydrology import Station


def stations_near_river(
    stations: list[Station], river_geojson_path: Path, buffer_meters: float = 1000.0
) -> list[Station]:
    """Filter `stations` to those within `buffer_meters` of the river geometry in a geojson file.

    Distance is computed in British National Grid (EPSG:27700) for accurate metres, since the EA
    hydrology API and most UK river geometries (e.g. OS Open Rivers extracts) are natively in
    lon/lat. Returned stations are sorted nearest-first.
    """
    river = gpd.read_file(river_geojson_path).to_crs(epsg=27700)
    river_line = river.union_all()

    located = [s for s in stations if s.lat is not None and s.long is not None]
    gdf = gpd.GeoDataFrame(
        {"station": located},
        geometry=[Point(s.long, s.lat) for s in located],
        crs="EPSG:4326",
    ).to_crs(epsg=27700)
    gdf["dist_m"] = gdf.geometry.distance(river_line)
    near = gdf[gdf["dist_m"] <= buffer_meters].sort_values("dist_m")
    return list(near["station"])


def join_stations_to_catchments(
    stations: list[Station], boundaries: list[CatchmentBoundary]
) -> list[tuple[Station, CatchmentBoundary]]:
    """Pair each station with its upstream catchment boundary, where both are known.

    Only stations that are also NRFA gauges carry a `nrfa_station_id`, and only ~671 of those
    have a boundary in the CAMELS-GB set (see `wxdecide.connectors.catchment_boundaries`) — so
    stations without either are silently dropped rather than erroring.
    """
    by_id = {b.nrfa_station_id: b for b in boundaries}
    return [
        (station, by_id[station.nrfa_station_id])
        for station in stations
        if station.nrfa_station_id is not None and station.nrfa_station_id in by_id
    ]


def union_catchment_boundaries(boundaries: list[CatchmentBoundary]) -> dict[str, Any]:
    """Union several catchment boundaries into one GeoJSON geometry.

    For a tidal station with no `nrfa_station_id` of its own (most WaterQualityStation-type
    Thames sites — see `wxdecide.schemas.ea_hydrology.Station`), its true drainage area is better
    approximated by combining the nearest upstream mainstem gauge's catchment (e.g. Kingston,
    NRFA 39001, for anything on the tidal Thames) with any tributary catchments that join the
    river between the tidal limit and that station — rather than reusing the mainstem gauge's
    catchment alone, which undercounts every tributary that joins downstream of it. Deciding
    *which* boundaries belong to a given station is a judgement call about confluence position
    that has to be made by the caller (e.g. per-station in a notebook); this just does the union.
    """
    polygons = [shape(b.geometry) for b in boundaries]
    return unary_union(polygons).__geo_interface__
