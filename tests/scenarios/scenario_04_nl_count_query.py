"""
Scenario 04 — NL COUNT Query Compilation
"Combien de capteurs sont hors service ?"
→ SELECT COUNT(*) FROM capteurs WHERE statut = :p1
"""

import pytest
from compiler.pipeline import NLToSQLPipeline


@pytest.fixture(scope="module")
def pipeline():
    return NLToSQLPipeline()


def test_count_capteurs_hors_service(pipeline):
    result = pipeline.compile_safe("combien de capteurs sont hors service")
    assert result["success"]
    sql = result["sql"].upper()
    assert "COUNT" in sql
    assert "CAPTEURS" in sql


def test_count_interventions(pipeline):
    result = pipeline.compile_safe("combien interventions")
    assert result["success"]
    assert "COUNT" in result["sql"].upper()


def test_count_produces_description(pipeline):
    result = pipeline.compile_safe("combien de capteurs")
    assert result["success"]
    assert result["description"]
    assert "compter" in result["description"].lower() or "nombre" in result["description"].lower()


def test_count_with_where_generates_where_clause(pipeline):
    result = pipeline.compile_safe("combien de capteurs dont statut est actif")
    assert result["success"]
    assert "WHERE" in result["sql"].upper()
    assert "statut" in result["sql"].lower()


def test_count_unknown_entity_fails(pipeline):
    result = pipeline.compile_safe("combien de pizzas")
    assert not result["success"]
    assert result["error"] is not None
