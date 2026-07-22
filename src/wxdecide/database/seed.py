"""Populate the local Postgres with 5 years of real UK river station data.

Pulls two sets of stations from the EA Hydrology API within a buffer of the River Thames
(`data/river_thames.geojson`, an OS Open Rivers extract):

1. Temperature/water-quality stations (`WITH_TEMPERATURE_TYPE`) — mostly WaterQualityStation
   barges with temperature, pH, conductivity, dissolved oxygen, etc.
2. River flow gauges (`RIVER_FLOW_TYPE`) — actual NRFA-eligible gauging stations that measure
   flow and level. These are the only stations that carry `nrfa_station_id` and can join to
   CAMELS-GB catchment boundary polygons (11 matches within the Thames corridor).

Plus 5 sample temperature stations nationally for baseline coverage. It then downloads readings
for *every* timeseries each station provides over the same fixed five-year window, shared across
every station and every measure. Readings are stored in long format — one row per (station,
timeseries, timestamp) — with the timeseries' parameter/period/statistic denormalised onto each
row from its `Measure` metadata, so it can be filtered/grouped on directly (e.g. in Metabase)
without a join.

The window is deliberately *shared* rather than anchored per-measure to each series' own latest
reading: individual sensors at EA gauging stations can go stale independently of each other (e.g.
one station's raw 15-min temperature probe stopped reporting in 2013 while its daily-aggregated
temperature stat kept going until 2025), so anchoring per-measure means different series end up
covering completely different periods and can't be compared. A shared window means a stale series
just comes back sparse or empty for that station — which is itself useful signal about what's
actually still live — while everything that IS returned lines up in time.

This is a large amount of data (multiple millions of rows, dominated by the live tidal Thames
stations' 15-minute series), so readings are upserted in bulk batches rather than one row at a
time. Schema is managed by Alembic, so run migrations first:

    uv run alembic upgrade head
    uv run python -m wxdecide.database.seed
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta
from itertools import islice
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session, select

from wxdecide.connectors.ea_hydrology import (
    EAHydrologyClient,
    RIVER_FLOW_TYPE,
    WITH_TEMPERATURE_TYPE,
)
from wxdecide.database.engine import get_engine
from wxdecide.database.tables import (
    MeasureTable,
    ReadingTable,
    StationStatusTable,
    StationTable,
    StationTypeTable,
)
from wxdecide.geo import stations_near_river
from wxdecide.schemas.ea_hydrology import Measure, Station

STATION_COLUMNS = {"id", "label", "river_name", "lat", "long", "nrfa_station_id"}

REPO_ROOT = Path(__file__).resolve().parents[3]
THAMES_GEOJSON_PATH = REPO_ROOT / "data" / "river_thames.geojson"
THAMES_BUFFER_METERS = 1000.0

SAMPLE_STATION_COUNT = 5
READING_WINDOW = timedelta(days=365 * 5)
READING_PAGE_SIZE = 5000
INSERT_BATCH_SIZE = 2000

# When a measure already has some readings stored, re-fetch only the date ranges not yet
# covered (plus this buffer on either side) rather than the whole window again. This is what
# makes a crashed or interrupted run resumable without re-downloading everything from scratch.
GAP_BUFFER = timedelta(days=7)


def _batched(rows: list[dict], size: int) -> Iterator[list[dict]]:
    it = iter(rows)
    while batch := list(islice(it, size)):
        yield batch


def seed() -> None:
    end_date = date.today()
    start_date = end_date - READING_WINDOW

    with EAHydrologyClient() as client, Session(get_engine()) as session:
        projection = "lat,long,type,status,measures(qualifier),riverName,label,nrfaStationID"

        # Temperature/water-quality stations (original selection)
        temp_stations = client.get_stations(
            params={"type": WITH_TEMPERATURE_TYPE, "_projection": projection}
        )
        sample_stations = temp_stations[:SAMPLE_STATION_COUNT]
        thames_temp = stations_near_river(
            temp_stations, THAMES_GEOJSON_PATH, THAMES_BUFFER_METERS
        )

        # River flow gauge stations — these are NRFA-eligible and can match catchment boundaries
        flow_stations = client.get_stations(
            params={"type": RIVER_FLOW_TYPE, "_projection": projection}
        )
        thames_flow = stations_near_river(
            flow_stations, THAMES_GEOJSON_PATH, THAMES_BUFFER_METERS
        )
        print(f"Thames flow gauges: {len(thames_flow)} (of {len(flow_stations)} nationally)")

        # Deduplicate and merge both sets
        seen_ids = {s.id for s in sample_stations}
        stations_to_seed = list(sample_stations)
        for s in thames_temp + thames_flow:
            if s.id not in seen_ids:
                seen_ids.add(s.id)
                stations_to_seed.append(s)

        for station in stations_to_seed:
            _upsert_station(session, station)
            session.commit()

            for measure_id in station.measure_ids:
                measure = client.get_measure(measure_id)
                _upsert_measure(session, measure, station.id)
                session.commit()

                n = _seed_measure_readings(
                    client, session, station.id, measure, start_date, end_date
                )
                session.commit()
                print(
                    f"  {station.label or station.id}: {measure.parameter} "
                    f"({measure.period_name}, {measure.value_type}) -> {n} readings"
                )

    print(f"Seeded {len(stations_to_seed)} stations over {start_date} to {end_date}.")


def _upsert_station(session: Session, station: Station) -> None:
    values = station.model_dump()

    station_values = {k: v for k, v in values.items() if k in STATION_COLUMNS}
    stmt = pg_insert(StationTable).values(**station_values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"], set_={k: v for k, v in station_values.items() if k != "id"}
    )
    session.execute(stmt)

    if station.types:
        stmt = pg_insert(StationTypeTable).values(
            [{"station_id": station.id, "type_uri": t} for t in station.types]
        )
        session.execute(stmt.on_conflict_do_nothing())

    if station.statuses:
        stmt = pg_insert(StationStatusTable).values(
            [{"station_id": station.id, "status_uri": s} for s in station.statuses]
        )
        session.execute(stmt.on_conflict_do_nothing())


def _upsert_measure(session: Session, measure: Measure, station_id: str) -> None:
    values = measure.model_dump()
    values["station_id"] = station_id
    stmt = pg_insert(MeasureTable).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"], set_={k: v for k, v in values.items() if k != "id"}
    )
    session.execute(stmt)


def _existing_coverage(session: Session, measure_id: str) -> tuple[date, date] | None:
    """Return the (min, max) date already stored for this measure, or `None` if it has no rows."""
    min_dt, max_dt = session.exec(
        select(func.min(ReadingTable.date_time), func.max(ReadingTable.date_time)).where(
            ReadingTable.measure_id == measure_id
        )
    ).one()
    if min_dt is None:
        return None
    return min_dt.date(), max_dt.date()


def _missing_ranges(
    existing: tuple[date, date] | None, start_date: date, end_date: date, buffer: timedelta
) -> list[tuple[date, date]]:
    """Which (sub-)ranges of [start_date, end_date] still need fetching, given what's stored.

    Assumes existing coverage for a measure is contiguous from its min to its max date — true for
    how this script fetches (a completed fetch grabs a contiguous span; a fetch interrupted
    mid-pagination grabs a contiguous prefix, since the API returns readings oldest-first). `buffer`
    is added on the fetched side of each gap so a resumed run overlaps its previous end rather than
    risking a subtle off-by-one hole at the boundary.
    """
    if existing is None:
        return [(start_date, end_date)]

    existing_min, existing_max = existing
    ranges = []

    if start_date < existing_min:
        ranges.append((start_date, min(existing_min + buffer, end_date)))

    if end_date > existing_max:
        ranges.append((max(existing_max - buffer, start_date), end_date))

    return ranges


def _seed_measure_readings(
    client: EAHydrologyClient,
    session: Session,
    station_id: str,
    measure: Measure,
    start_date: date,
    end_date: date,
) -> int:
    existing = _existing_coverage(session, measure.id)
    ranges = _missing_ranges(existing, start_date, end_date, GAP_BUFFER)
    if not ranges:
        return 0

    total = 0
    for range_start, range_end in ranges:
        readings = client.get_readings(
            measure.id,
            params={"min-date": range_start.isoformat(), "max-date": range_end.isoformat()},
            page_size=READING_PAGE_SIZE,
        )
        if not readings:
            continue

        rows = [
            {
                "measure_id": measure.id,
                "date_time": reading.date_time,
                "value": reading.value,
                "quality": reading.quality,
                "station_id": station_id,
                "parameter": measure.parameter,
                "period": measure.period,
                "period_name": measure.period_name,
                "value_type": measure.value_type,
                "unit_name": measure.unit_name,
            }
            for reading in readings
        ]
        for batch in _batched(rows, INSERT_BATCH_SIZE):
            stmt = pg_insert(ReadingTable).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["measure_id", "date_time"],
                set_={"value": stmt.excluded.value, "quality": stmt.excluded.quality},
            )
            session.execute(stmt)
        total += len(rows)
    return total


if __name__ == "__main__":
    seed()
