"""Pydantic model for an OS Open Rivers watercourse link.

`watercourse_link` is OS Open Rivers' line-network layer: one row per mapped stretch of
watercourse, noded at confluences so `start_node`/`end_node` describe network topology.
Rivers are rarely tagged with a single consistent name throughout their length — `River Thames`
covers the tidal reach and the lock-free stretches, but many pool/reach sections between locks
carry a local name (e.g. `Sonning Reach`) with `River Thames` recorded only in
`watercourse_name_alternative`. Filtering on either field is needed to select a named river's
full extent.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RiverLink(BaseModel):
    """A single watercourse link from the OS Open Rivers `watercourse_link` layer."""

    id: str
    watercourse_name: str | None = None
    watercourse_name_alternative: str | None = None
    form: str | None = None
    flow_direction: str | None = None
    fictitious: str | None = None
    length: float | None = None
    start_node: str | None = None
    end_node: str | None = None
    geometry: dict[str, Any]
