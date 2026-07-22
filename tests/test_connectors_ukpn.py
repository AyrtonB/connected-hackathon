import httpx

from wxdecide.connectors.ukpn import UKPNClient


def _mock_transport(dataset_id: str, results: list[dict]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(f"/{dataset_id}/records")
        return httpx.Response(200, json={"total_count": len(results), "results": results})

    return httpx.MockTransport(handler)


def test_get_live_faults():
    results = [
        {
            "incidentreference": "INCD-1",
            "powercuttype": "Unplanned",
            "creationdatetime": "2026-07-21T08:08:00+00:00",
            "nocallsreported": 44,
            "nocustomeraffected": 210,
            "postcodesaffected": "N15",
            "incidentdescription": "A fault occurred.",
            "incidentcategory": "Cable Fault",
            "incidenttype": 1,
            "incidentpriority": 2,
            "statusid": 3,
            "restoreddatetime": None,
            "estimatedrestorationdate": None,
            "geopoint": {"lon": -0.08, "lat": 51.6},
            "operatingzone": "LPN",
        }
    ]

    with UKPNClient(transport=_mock_transport("ukpn-live-faults", results)) as client:
        faults = client.get_live_faults(limit=10)

    assert len(faults) == 1
    assert faults[0].incident_reference == "INCD-1"


def test_get_interruption_incidents():
    results = [
        {
            "incident_reference": "IIS-1",
            "restoration_stage": 3,
            "start_date_time": "2025-11-15T18:30:00+00:00",
            "end_date_time": "2025-11-15T22:05:00+00:00",
            "customers_restored": 850,
            "cause_code": "Weather - Wind",
            "ee_coding": "Y",
            "licence_area": "EPN",
            "regulatory_year": "2025/26",
        }
    ]

    with UKPNClient(transport=_mock_transport("ukpn-iis", results)) as client:
        incidents = client.get_interruption_incidents(limit=10)

    assert len(incidents) == 1
    assert incidents[0].cause_code == "Weather - Wind"
    assert incidents[0].exceptional_event == "Y"
