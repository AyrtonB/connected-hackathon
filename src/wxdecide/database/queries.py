"""Hand-written queries over `river_links` that don't map cleanly to plain ORM filtering.

`river_links` holds the raw OS Open Rivers network as-is; picking a single named river back out
of it is more than a `WHERE watercourse_name = ...` filter (see `wxdecide.schemas.rivers`), so
that logic lives here rather than being reconstructed ad hoc wherever it's needed.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlmodel import Session, select

from wxdecide.database.tables import RiverLinkTable

DEFAULT_MAX_GAP_LENGTH = 1000.0

# Same logic as the `river_thames_connected` view (see the `index river_links nodes and add
# connected thames view` migration), parameterised by river name/gap length rather than hardcoded
# to the Thames at 1000m: start from links named `:river_name` (in either `watercourse_name` or
# `watercourse_name_alternative` — many reach/pool sections only carry the river name in the
# latter), then recursively pull in *unnamed* links no longer than `:max_gap_length` metres that
# directly bridge two already-included nodes. Real named tributaries never match the "unnamed"
# recursive step, so they aren't pulled in even though they touch the same nodes.
_CONNECTED_RIVER_LINKS_SQL = text(
    """
    WITH RECURSIVE named_links AS (
        SELECT id, start_node, end_node
        FROM river_links
        WHERE watercourse_name = :river_name
           OR watercourse_name_alternative = :river_name
    ),
    bridging(id, start_node, end_node) AS (
        SELECT rl.id, rl.start_node, rl.end_node
        FROM river_links rl
        WHERE rl.watercourse_name IS NULL
          AND rl.watercourse_name_alternative IS NULL
          AND rl.length <= :max_gap_length
          AND (
              rl.start_node IN (SELECT start_node FROM named_links UNION SELECT end_node FROM named_links)
              OR rl.end_node IN (SELECT start_node FROM named_links UNION SELECT end_node FROM named_links)
          )

        UNION

        SELECT rl.id, rl.start_node, rl.end_node
        FROM river_links rl
        JOIN bridging b
          ON rl.start_node IN (b.start_node, b.end_node)
          OR rl.end_node IN (b.start_node, b.end_node)
        WHERE rl.watercourse_name IS NULL
          AND rl.watercourse_name_alternative IS NULL
          AND rl.length <= :max_gap_length
    )
    SELECT rl.*
    FROM river_links rl
    WHERE rl.id IN (SELECT id FROM named_links)
       OR rl.id IN (SELECT id FROM bridging)
    """
)


def connected_river_links(
    session: Session,
    river_name: str,
    max_gap_length: float = DEFAULT_MAX_GAP_LENGTH,
) -> list[RiverLinkTable]:
    """Return every `RiverLinkTable` row that makes up `river_name`'s full, gap-bridged course.

    Equivalent to `SELECT * FROM river_thames_connected` when `river_name="River Thames"` and
    `max_gap_length=1000.0`, but works for any river and lets the gap threshold be tuned — a
    smaller/larger `max_gap_length` trades off closing real lock/weir/tidal gaps against
    accidentally bridging into an unrelated unnamed watercourse nearby.
    """
    stmt = (
        select(RiverLinkTable)
        .from_statement(_CONNECTED_RIVER_LINKS_SQL)
        .params(river_name=river_name, max_gap_length=max_gap_length)
    )
    return list(session.execute(stmt).scalars())
