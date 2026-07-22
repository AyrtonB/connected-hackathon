"""Populate the local Postgres with CAMELS-GB catchment boundary polygons.

Loads all 671 catchment boundaries — a static, open-access reference dataset (see
`wxdecide.connectors.catchment_boundaries`) — independent of which EA hydrology stations have
been seeded. Join to `stations` via `StationTable.nrfa_station_id ==
CatchmentBoundaryTable.nrfa_station_id` at query time; a station only has a matching boundary if
it's also an NRFA gauge included in the 671-catchment CAMELS-GB set.

Schema is managed by Alembic, so run migrations first:

    uv run alembic upgrade head
    uv run python -m wxdecide.database.seed_catchments
"""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

from wxdecide.connectors.catchment_boundaries import fetch_camels_gb_boundaries
from wxdecide.database.engine import get_engine
from wxdecide.database.tables import CatchmentBoundaryTable


def seed() -> None:
    boundaries = fetch_camels_gb_boundaries()
    with Session(get_engine()) as session:
        for boundary in boundaries:
            values = boundary.model_dump()
            stmt = pg_insert(CatchmentBoundaryTable).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["nrfa_station_id"],
                set_={k: v for k, v in values.items() if k != "nrfa_station_id"},
            )
            session.execute(stmt)
        session.commit()
    print(f"Seeded {len(boundaries)} catchment boundaries.")


if __name__ == "__main__":
    seed()
