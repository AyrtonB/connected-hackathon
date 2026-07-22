import json

from shapely.geometry import shape

from wxdecide.geo import stations_near_river, union_catchment_boundaries
from wxdecide.schemas.catchment import CatchmentBoundary
from wxdecide.schemas.ea_hydrology import Station


def _station(id_: str, lon: float, lat: float) -> Station:
    return Station.model_validate({"@id": id_, "long": lon, "lat": lat})


def test_stations_near_river_filters_by_distance(tmp_path):
    # A short straight "river" running north along a fixed longitude near London.
    river_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-0.1, 51.4], [-0.1, 51.6]],
                },
            }
        ],
    }
    path = tmp_path / "river.geojson"
    path.write_text(json.dumps(river_geojson))

    on_river = _station("near", -0.1, 51.5)
    far_away = _station("far", -1.5, 51.5)

    result = stations_near_river([on_river, far_away], path, buffer_meters=100.0)

    assert [s.id for s in result] == ["near"]


def test_stations_near_river_skips_stations_without_coordinates(tmp_path):
    river_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-0.1, 51.4], [-0.1, 51.6]],
                },
            }
        ],
    }
    path = tmp_path / "river.geojson"
    path.write_text(json.dumps(river_geojson))

    no_coords = Station.model_validate({"@id": "no-coords"})

    result = stations_near_river([no_coords], path, buffer_meters=100.0)

    assert result == []


def test_union_catchment_boundaries_combines_disjoint_polygons():
    # Two adjacent 1x1 squares, like a mainstem catchment and a tributary joining it.
    mainstem = CatchmentBoundary(
        nrfa_station_id="mainstem",
        area_km2=1.0,
        geometry={"type": "Polygon", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]},
    )
    tributary = CatchmentBoundary(
        nrfa_station_id="tributary",
        area_km2=1.0,
        geometry={"type": "Polygon", "coordinates": [[(1, 0), (2, 0), (2, 1), (1, 1), (1, 0)]]},
    )

    unioned = union_catchment_boundaries([mainstem, tributary])
    geom = shape(unioned)

    assert geom.area == 2.0
    assert geom.contains(shape({"type": "Point", "coordinates": (0.5, 0.5)}))
    assert geom.contains(shape({"type": "Point", "coordinates": (1.5, 0.5)}))


def test_union_catchment_boundaries_single_input_is_unchanged():
    only = CatchmentBoundary(
        nrfa_station_id="only",
        area_km2=1.0,
        geometry={"type": "Polygon", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]},
    )

    unioned = union_catchment_boundaries([only])

    assert shape(unioned).area == 1.0
