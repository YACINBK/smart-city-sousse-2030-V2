import json

from ai.client import MockLLMClient
from ai.prompts.report_templates import AIR_QUALITY_REPORT, GENERAL_RECOMMENDATIONS


def test_mock_air_report_is_structured():
    client = MockLLMClient()
    prompt = AIR_QUALITY_REPORT.format(period="01/04/2026 - 25/04/2026", data_summary="| Zone | PM2.5 |")
    text = client.complete(prompt)
    assert "Rapport Qualite de l'Air" in text
    assert "Resume executif" in text


def test_mock_priority_actions_returns_json_payload():
    client = MockLLMClient()
    prompt = GENERAL_RECOMMENDATIONS.format(
        hors_service_count=3,
        pending_interventions=7,
        critical_alerts=2,
        critical_zones=1,
        vehicles_breakdown=0,
    )
    text = client.complete(prompt)
    data = json.loads(text)
    assert data["actions"]
    assert data["niveau_urgence"] == "ORANGE"
    assert "justification" in data["actions"][0]
    assert "indicateur_succes" in data["actions"][0]
