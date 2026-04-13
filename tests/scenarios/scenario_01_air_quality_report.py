"""
Scenario 01 — Air Quality Report Generation (AI module)
Verifies ReportGenerator.generate() returns structured Markdown reports.
Uses MockLLMClient (no API key needed) and mocked DB context.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch
from ai.report_generator import ReportGenerator
from ai.context_builder import DBContextBuilder


_MOCK_TABLE = "| Zone | PM2.5 | PM10 |\n|------|-------|------|\n| Médina | 42.1 | 65.3 |"
_MOCK_STATS = {
    "hors_service_count": 2, "pending_interventions": 5,
    "critical_alerts": 1, "critical_zones": 2, "vehicles_breakdown": 0,
}


@pytest.fixture(scope="module")
def gen():
    return ReportGenerator()


def test_air_quality_report_not_empty(gen):
    with patch.object(DBContextBuilder, 'air_quality_summary', return_value=_MOCK_TABLE):
        report = gen.generate("qualite_air",
                              start=date.today() - timedelta(days=7),
                              end=date.today())
    assert report and len(report) > 20


def test_air_quality_report_is_string(gen):
    with patch.object(DBContextBuilder, 'air_quality_summary', return_value=_MOCK_TABLE):
        report = gen.generate("qualite_air")
    assert isinstance(report, str)


def test_intervention_report(gen):
    with patch.object(DBContextBuilder, 'intervention_summary', return_value=_MOCK_TABLE):
        report = gen.generate("interventions")
    assert isinstance(report, str) and len(report) > 10


def test_capteurs_report(gen):
    with patch.object(DBContextBuilder, 'sensor_status_summary', return_value=_MOCK_TABLE):
        report = gen.generate("capteurs")
    assert isinstance(report, str) and len(report) > 10


def test_recommendations_report(gen):
    with patch.object(DBContextBuilder, 'quick_stats', return_value=_MOCK_STATS):
        report = gen.generate("recommandations")
    assert isinstance(report, str) and len(report) > 10


def test_unknown_report_type(gen):
    report = gen.generate("unknown_type")
    assert "inconnu" in report.lower() or "type" in report.lower()


def test_explain_sql(gen):
    explanation = gen.explain_sql("SELECT COUNT(*) FROM capteurs WHERE statut='HORS_SERVICE'")
    assert explanation and isinstance(explanation, str)
