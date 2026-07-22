"""Client for UK Power Networks' open data portal.

UKPN publish their open data via an OpenDataSoft Explore API (v2.1). This client wraps the
two datasets relevant to the power-outage-forecast concept (see docs/ideation.md):

- `ukpn-live-faults`: near real-time power cuts (continuously updated).
- `ukpn-iis`: historical fault records under Ofgem's Interruptions Incentive Scheme, including
  a cause code and an "exceptional (weather) event" flag per incident (updated annually).
"""

from __future__ import annotations

from typing import Any, Self

import httpx

from wxdecide.schemas.ukpn import InterruptionIncident, LiveFault

BASE_URL = "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets"

LIVE_FAULTS_DATASET = "ukpn-live-faults"
INTERRUPTIONS_DATASET = "ukpn-iis"


class UKPNClient:
    """Thin client over UKPN's OpenDataSoft Explore API v2.1."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _get_records(
        self,
        dataset_id: str,
        *,
        limit: int,
        offset: int,
        where: str | None,
        order_by: str | None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if where:
            params["where"] = where
        if order_by:
            params["order_by"] = order_by
        response = self._client.get(f"/{dataset_id}/records", params=params)
        response.raise_for_status()
        return response.json()["results"]

    def get_live_faults(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        where: str | None = None,
        order_by: str | None = "creationdatetime desc",
    ) -> list[LiveFault]:
        """Fetch current/recent incidents from the live faults feed.

        `where` accepts an OpenDataSoft Query Language (ODSQL) filter, e.g.
        `where="operatingzone='LPN'"`.
        """
        records = self._get_records(
            LIVE_FAULTS_DATASET, limit=limit, offset=offset, where=where, order_by=order_by
        )
        return [LiveFault.model_validate(record) for record in records]

    def get_interruption_incidents(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        where: str | None = None,
        order_by: str | None = "start_date_time desc",
    ) -> list[InterruptionIncident]:
        """Fetch historical, weather-flagged fault records from the Interruptions Incentive Scheme."""
        records = self._get_records(
            INTERRUPTIONS_DATASET, limit=limit, offset=offset, where=where, order_by=order_by
        )
        return [InterruptionIncident.model_validate(record) for record in records]
