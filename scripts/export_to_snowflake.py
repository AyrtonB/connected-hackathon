"""Export Postgres tables to Parquet files for Snowflake upload.

Connects to the local Postgres (via docker-compose), exports each table to a Parquet file in
`exports/`. Geometry columns are converted to WKT strings so Snowflake can parse them with
ST_GEOGRAPHYFROMWKT() or TRY_TO_GEOGRAPHY() at COPY INTO time.

Usage:
    uv run python scripts/export_to_snowflake.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from wxdecide.database.engine import get_engine

EXPORT_DIR = Path(__file__).resolve().parent / "exports"

TABLES = [
    "stations",
    "station_types",
    "station_statuses",
    "measures",
    "readings",
    "river_links",
    "catchment_boundaries",
]


def export_table(engine, table_name: str, export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)

    if table_name == "river_links":
        # Convert PostGIS geometry to WKT string
        query = text("""
            SELECT id, watercourse_name, watercourse_name_alternative,
                   form, flow_direction, fictitious, length, start_node, end_node,
                   ST_AsText(geometry) AS geometry_wkt
            FROM river_links
        """)
    elif table_name == "catchment_boundaries":
        # geometry is already a JSON dict — cast to text for Snowflake TRY_TO_GEOGRAPHY()
        query = text("""
            SELECT nrfa_station_id, area_km2,
                   geometry::text AS geometry_geojson
            FROM catchment_boundaries
        """)
    else:
        query = text(f"SELECT * FROM {table_name}")  # noqa: S608

    df = pd.read_sql(query, engine)
    out_path = export_dir / f"{table_name}.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  {table_name}: {len(df)} rows -> {out_path.name}")
    return out_path


def main() -> None:
    engine = get_engine()
    print(f"Exporting to {EXPORT_DIR}/")
    for table_name in TABLES:
        export_table(engine, table_name, EXPORT_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
