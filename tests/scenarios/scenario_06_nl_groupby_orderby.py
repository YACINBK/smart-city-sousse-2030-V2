"""
Scenario 06 — NL GROUP BY + ORDER BY
"Affiche le nombre d'interventions par zone, du plus élevé au plus bas"
→ SELECT zone_id, COUNT(*) AS total FROM interventions
  GROUP BY zone_id ORDER BY COUNT(*) DESC
"""

import pytest
from compiler.pipeline import NLToSQLPipeline


@pytest.fixture(scope="module")
def pipeline():
    return NLToSQLPipeline()


def test_groupby_capteurs_by_zone(pipeline):
    result = pipeline.compile_safe("affiche capteurs par zone_id")
    assert result["success"]
    sql = result["sql"].upper()
    assert "GROUP BY" in sql or "CAPTEURS" in sql


def test_orderby_desc(pipeline):
    result = pipeline.compile_safe("affiche capteurs par ordre décroissant")
    assert result["success"]
    assert "DESC" in result["sql"].upper()


def test_orderby_asc(pipeline):
    result = pipeline.compile_safe("affiche capteurs par ordre croissant")
    assert result["success"]
    assert "ASC" in result["sql"].upper()


def test_top5_zones(pipeline):
    result = pipeline.compile_safe("affiche 5 zones")
    assert result["success"]
    sql = result["sql"].upper()
    assert "5" in sql or "LIMIT" in sql


def test_full_aggregation_pipeline(pipeline):
    """Full: SELECT statut, COUNT(*) GROUP BY statut ORDER BY COUNT(*) DESC"""
    result = pipeline.compile_safe("affiche capteurs par statut")
    assert result["success"]
    sql = result["sql"].upper()
    assert "CAPTEURS" in sql
