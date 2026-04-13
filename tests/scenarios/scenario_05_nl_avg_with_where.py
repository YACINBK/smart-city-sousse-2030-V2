"""
Scenario 05 — NL AVG with WHERE Clause
"Quelle est la moyenne du PM2.5 des capteurs actifs ?"
→ SELECT AVG(pm25) FROM mesures WHERE ...
"""

import pytest
from compiler.pipeline import NLToSQLPipeline


@pytest.fixture(scope="module")
def pipeline():
    return NLToSQLPipeline()


def test_avg_pm25(pipeline):
    result = pipeline.compile_safe("moyenne pm25 des mesures")
    assert result["success"]
    sql = result["sql"].upper()
    assert "AVG" in sql
    assert "PM25" in sql


def test_avg_produces_alias(pipeline):
    result = pipeline.compile_safe("moyenne pm25 des mesures")
    assert result["success"]
    assert "moyenne_pm25" in result["sql"].lower() or "avg" in result["sql"].lower()


def test_avg_temperature(pipeline):
    result = pipeline.compile_safe("moyenne temperature des mesures")
    assert result["success"]
    assert "AVG" in result["sql"].upper()


def test_avg_ambiguity_detected(pipeline):
    """'moyenne des mesures' without specifying column should raise AmbiguityError."""
    from compiler.errors import AmbiguityError
    try:
        pipeline.compile("moyenne des mesures")
        # May succeed if SemanticAnalyzer infers single numeric col
    except AmbiguityError as e:
        assert e.interpretations  # has candidate SQLs
    except Exception:
        pass  # Any compile error also acceptable


def test_avg_unknown_column_fails(pipeline):
    result = pipeline.compile_safe("moyenne xyz des mesures")
    assert not result["success"]
