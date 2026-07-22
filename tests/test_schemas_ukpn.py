from wxdecide.schemas.ukpn import InterruptionIncident, LiveFault


def test_live_fault_parses_aliased_fields():
    raw = {
        "incidentreference": "INCD-619132-Z",
        "powercuttype": "Unplanned",
        "creationdatetime": "2026-07-21T08:08:00+00:00",
        "nocallsreported": 44,
        "nocustomeraffected": 210,
        "postcodesaffected": "N15, N8",
        "incidentdescription": "A fault occurred on an underground electricity cable.",
        "incidentcategory": "Cable Fault",
        "incidenttype": 1,
        "incidentpriority": 2,
        "statusid": 3,
        "restoreddatetime": "2026-07-21T22:20:00+00:00",
        "estimatedrestorationdate": None,
        "geopoint": {"lon": -0.0827, "lat": 51.6},
        "operatingzone": "LPN",
    }

    fault = LiveFault.model_validate(raw)

    assert fault.incident_reference == "INCD-619132-Z"
    assert fault.no_customers_affected == 210
    assert fault.geopoint is not None
    assert fault.geopoint.lat == 51.6
    assert fault.operating_zone == "LPN"


def test_interruption_incident_parses_aliased_fields():
    raw = {
        "incident_reference": "IIS-2025-000123",
        "restoration_stage": 3,
        "start_date_time": "2025-11-15T18:30:00+00:00",
        "end_date_time": "2025-11-15T22:05:00+00:00",
        "customers_restored": 850,
        "reinteruption_stage": None,
        "mei_code": "OHL",
        "cause_code": "Weather - Wind",
        "cont_cause_code": None,
        "damage": 1,
        "ee_coding": "Y",
        "incident_count": 1,
        "licence_area": "EPN",
        "regulatory_year": "2025/26",
        "substation": "Example Primary",
        "sitefunctionallocation": "EX-001",
        "spatial_coordinates": {"lon": 0.481, "lat": 51.746},
    }

    incident = InterruptionIncident.model_validate(raw)

    assert incident.incident_reference == "IIS-2025-000123"
    assert incident.cause_code == "Weather - Wind"
    assert incident.exceptional_event == "Y"
    assert incident.site_functional_location == "EX-001"
    assert incident.spatial_coordinates is not None
    assert incident.spatial_coordinates.lon == 0.481
