"""Load the full OS Open Rivers (GB) watercourse network into Postgres/PostGIS.

Loads every link in `data/os_open_rivers_gb.geojson.gz` (~193k rows — see `nbs/02-river-geo.ipynb`
for how it was sourced) into `river_links` as native PostGIS geometry, so it can be queried and
filtered in SQL rather than re-parsed from GeoJSON in Python each time. See the `river_thames`
view (added by the `add river_links table with postgis` migration) for an example: it selects the
Thames out of this table by name.

Schema is managed by Alembic, so run migrations first:

    uv run alembic upgrade head
    uv run python -m wxdecide.database.seed_rivers
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from itertools import islice
from pathlib import Path
from typing import Any

import geopandas as gpd
from geoalchemy2.shape import from_shape
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

from wxdecide.database.engine import get_engine
from wxdecide.database.tables import RiverLinkTable

REPO_ROOT = Path(__file__).resolve().parents[3]
RIVERS_GEOJSON_PATH = REPO_ROOT / "data" / "os_open_rivers_gb.geojson.gz"

ATTRIBUTE_COLUMNS = [
    "id",
    "watercourse_name",
    "watercourse_name_alternative",
    "form",
    "flow_direction",
    "fictitious",
    "length",
    "start_node",
    "end_node",
]
INSERT_BATCH_SIZE = 2000


def _batched(rows: list[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    it = iter(rows)
    while batch := list(islice(it, size)):
        yield batch


def _clean(value: Any) -> Any:
    # GeoPandas/pandas represent a missing string as float NaN rather than None — left as-is, a
    # VARCHAR column would happily (and wrongly) store the literal text "NaN".
    return None if isinstance(value, float) and math.isnan(value) else value


def seed() -> None:
    rivers = gpd.read_file(f"/vsigzip/{RIVERS_GEOJSON_PATH}")

    rows = [
        {
            **{col: _clean(getattr(row, col)) for col in ATTRIBUTE_COLUMNS},
            "geometry": from_shape(row.geometry, srid=4326),
        }
        for row in rivers.itertuples()
    ]

    with Session(get_engine()) as session:
        for batch in _batched(rows, INSERT_BATCH_SIZE):
            stmt = pg_insert(RiverLinkTable).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={col: stmt.excluded[col] for col in batch[0] if col != "id"},
            )
            session.execute(stmt)
        session.commit()

    print(f"Seeded {len(rows)} river links.")


if __name__ == "__main__":
    seed()
