"""SQLModel table definitions.

Each table extends the corresponding plain Pydantic schema in `wxdecide.schemas.ea_hydrology`
with the bits SQLModel needs for persistence: a table name, primary key(s), and explicit
SQLAlchemy column types for fields (like the list-of-URI fields on `Station`) that don't have
an obvious default column type.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from wxdecide.schemas.catchment import CatchmentBoundary
from wxdecide.schemas.ea_hydrology import Measure, Reading
from wxdecide.schemas.rivers import RiverLink


class StationTable(SQLModel, table=True):
    """Persisted form of `Station`'s scalar fields, keyed on its hydrology API station URI.

    Deliberately doesn't inherit `wxdecide.schemas.ea_hydrology.Station` directly: that model's
    `types`/`statuses`/`measure_ids` are lists validated by a `field_validator` scoped to those
    field names, which Pydantic won't let a subclass remove fields for. More importantly, flatten-
    ing those lists lossily into this table would lose real information — a single `status` column
    would silently drop cases like Bredon's simultaneous `statusSuspended` + `statusFlowSuspended`
    (exactly why its flow measures return zero readings while its level measures don't), and
    `measure_ids` is genuinely one-to-many. They're kept at full fidelity in
    `StationTypeTable`/`StationStatusTable`/`MeasureTable` instead.
    """

    __tablename__ = "stations"

    id: str = Field(primary_key=True)
    label: str | None = None
    river_name: str | None = Field(default=None, index=True)
    lat: float | None = None
    long: float | None = None
    nrfa_station_id: str | None = Field(default=None, index=True)


class StationTypeTable(SQLModel, table=True):
    """One row per (station, type URI) — the full `Station.types` list, normalised.

    A station can carry several types simultaneously (e.g. `RiverStation` + `WithTemperature` +
    `WaterQualityStation`), so this is a proper one-to-many join table rather than a single column.
    """

    __tablename__ = "station_types"

    station_id: str = Field(foreign_key="stations.id", primary_key=True)
    type_uri: str = Field(primary_key=True)


class StationStatusTable(SQLModel, table=True):
    """One row per (station, status URI) — the full `Station.statuses` list, normalised.

    Kept as a join table rather than a single `status` column deliberately: some stations report
    more than one status at once — e.g. Bredon has both `statusSuspended` and
    `statusFlowSuspended`, which is exactly why its flow measures return zero readings while its
    level measures don't. Collapsing to one column would lose that signal.
    """

    __tablename__ = "station_statuses"

    station_id: str = Field(foreign_key="stations.id", primary_key=True)
    status_uri: str = Field(primary_key=True)


class MeasureTable(Measure, SQLModel, table=True):
    """Persisted form of `Measure` — one row per timeseries a station provides.

    Seeded for every measure a station has, regardless of whether it produced any readings in the
    currently-loaded window. This is what makes "this measure exists but is currently dead" (e.g.
    a station whose sensor stopped reporting years ago) a queryable fact rather than something
    only visible by re-fetching the live API.
    """

    __tablename__ = "measures"

    id: str = Field(primary_key=True)
    station_id: str | None = Field(default=None, foreign_key="stations.id", index=True)


class CatchmentBoundaryTable(CatchmentBoundary, SQLModel, table=True):
    """Persisted form of `CatchmentBoundary`, keyed on NRFA station id.

    Not linked to `stations` via a foreign key: this is a static reference dataset (CAMELS-GB)
    seeded independently of which EA stations happen to be loaded, so it may contain ids for
    stations not yet — or never — present in `stations`. Join on `nrfa_station_id` at query time.
    """

    __tablename__ = "catchment_boundaries"

    nrfa_station_id: str = Field(primary_key=True)
    geometry: dict = Field(sa_column=Column(JSON))


class RiverLinkTable(RiverLink, SQLModel, table=True):
    """Persisted form of `RiverLink`, keyed on the OS Open Rivers link id.

    `geometry` is stored as a native PostGIS `LINESTRING` (WGS84, SRID 4326) rather than JSON, so
    it can be queried/indexed spatially (e.g. `ST_DWithin` to find links near a point) — see
    `wxdecide.database.seed_rivers` for how GeoJSON geometries are converted on insert.
    """

    __tablename__ = "river_links"

    id: str = Field(primary_key=True)
    watercourse_name: str | None = Field(default=None, index=True)
    watercourse_name_alternative: str | None = Field(default=None, index=True)
    start_node: str | None = Field(default=None, index=True)
    end_node: str | None = Field(default=None, index=True)
    geometry: Any = Field(sa_column=Column(Geometry(geometry_type="LINESTRING", srid=4326)))


class ReadingTable(Reading, SQLModel, table=True):
    """Long-format persisted form of `Reading`: one row per (station, timeseries, timestamp).

    A reading is uniquely identified by which measure (time series) it belongs to plus its
    timestamp, so those two fields form a composite primary key rather than a synthetic id.
    `station_id` and the `parameter`/`period`/`value_type`/`unit_name` attributes aren't part of
    the API's reading payload — they're denormalised on at ingest time from that measure's own
    metadata (`Measure`), so rows can be filtered/grouped by attribute (e.g. `parameter = 'FLOW'`)
    without a join.
    """

    __tablename__ = "readings"

    measure_id: str = Field(primary_key=True)
    date_time: datetime = Field(primary_key=True)
    value: float | None = None
    station_id: str | None = Field(default=None, foreign_key="stations.id", index=True)
    parameter: str = Field(index=True)
    period: int
    period_name: str | None = None
    value_type: str | None = None
    unit_name: str | None = None
