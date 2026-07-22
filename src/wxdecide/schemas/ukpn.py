"""Pydantic models for UK Power Networks open datasets.

Field names/types are taken from the OpenDataSoft Explore API v2.1 catalog metadata for
`ukpn-live-faults` and `ukpn-iis` (see docs/ideation.md for how these are used).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GeoPoint(BaseModel):
    """A latitude/longitude pair, as returned by OpenDataSoft's `geo_point_2d` field type."""

    lon: float
    lat: float


class LiveFault(BaseModel):
    """A single record from the `ukpn-live-faults` dataset (near real-time power cuts).

    Geopoints in this dataset are aggregated from postcode data to protect customer privacy.
    """

    model_config = ConfigDict(populate_by_name=True)

    incident_reference: str = Field(alias="incidentreference")
    power_cut_type: str | None = Field(default=None, alias="powercuttype")
    creation_datetime: datetime | None = Field(default=None, alias="creationdatetime")
    no_calls_reported: int | None = Field(default=None, alias="nocallsreported")
    no_customers_affected: int | None = Field(default=None, alias="nocustomeraffected")
    postcodes_affected: str | None = Field(default=None, alias="postcodesaffected")
    incident_description: str | None = Field(default=None, alias="incidentdescription")
    incident_category: str | None = Field(default=None, alias="incidentcategory")
    incident_type: int | None = Field(default=None, alias="incidenttype")
    incident_priority: int | None = Field(default=None, alias="incidentpriority")
    status_id: int | None = Field(default=None, alias="statusid")
    restored_datetime: datetime | None = Field(default=None, alias="restoreddatetime")
    estimated_restoration_date: datetime | None = Field(
        default=None, alias="estimatedrestorationdate"
    )
    geopoint: GeoPoint | None = None
    operating_zone: str | None = Field(default=None, alias="operatingzone")


class InterruptionIncident(BaseModel):
    """A single historical record from `ukpn-iis` (Ofgem Interruptions Incentive Scheme).

    Includes a cause code and an "exceptional event" flag per incident, which is what makes
    this dataset useful as ground truth for correlating outages with severe weather.
    """

    model_config = ConfigDict(populate_by_name=True)

    incident_reference: str
    restoration_stage: int | None = None
    start_date_time: datetime | None = None
    end_date_time: datetime | None = None
    customers_restored: int | None = None
    reinterruption_stage: str | None = Field(default=None, alias="reinteruption_stage")
    mei_code: str | None = None
    cause_code: str | None = None
    cont_cause_code: str | None = None
    damage: int | None = None
    exceptional_event: str | None = Field(default=None, alias="ee_coding")
    incident_count: int | None = None
    licence_area: str | None = None
    regulatory_year: str | None = None
    substation: str | None = None
    site_functional_location: str | None = Field(default=None, alias="sitefunctionallocation")
    spatial_coordinates: GeoPoint | None = None
