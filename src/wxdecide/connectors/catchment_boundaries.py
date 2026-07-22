"""Connector for CAMELS-GB catchment boundaries (NRFA gauging-station upstream catchments).

Source: CAMELS-GB v1 (Coxon et al. 2020), published on UKCEH's Environmental Information Data
Centre — open access under the Open Government Licence, no registration required. Ships a
shapefile of upstream catchment polygons for 671 NRFA gauging stations, keyed by NRFA station id.

Docs: https://catalogue.ceh.ac.uk/id/8344e4f3-d2ea-44f5-8afa-86d2987543a9
"""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import httpx

from wxdecide.schemas.catchment import CatchmentBoundary

BASE_URL = "https://catalogue.ceh.ac.uk/datastore/eidchub/8344e4f3-d2ea-44f5-8afa-86d2987543a9"
BOUNDARIES_ZIP_URL = f"{BASE_URL}/CAMELS_GB_catchment_boundaries.zip"
SHAPEFILE_NAME = "CAMELS_GB_catchment_boundaries.shp"


def fetch_camels_gb_boundaries(*, timeout: float = 60.0) -> list[CatchmentBoundary]:
    """Download and parse the CAMELS-GB catchment boundary shapefile.

    Catchment area is computed in the shapefile's native British National Grid (EPSG:27700, so
    it's in accurate metres) before the geometry is reprojected to WGS84 for storage, matching
    the lon/lat used elsewhere in this project (e.g. `Station.lat`/`Station.long`).
    """
    response = httpx.get(BOUNDARIES_ZIP_URL, timeout=timeout, follow_redirects=True)
    response.raise_for_status()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            zf.extractall(tmp_path)
        gdf = gpd.read_file(tmp_path / SHAPEFILE_NAME)

    area_km2 = gdf.geometry.area / 1e6
    gdf = gdf.to_crs(epsg=4326)

    return [
        CatchmentBoundary(
            nrfa_station_id=id_string,
            area_km2=area,
            geometry=geometry.__geo_interface__,
        )
        for id_string, area, geometry in zip(gdf["ID_STRING"], area_km2, gdf.geometry, strict=True)
    ]
