"""Unit tests for the full compilation pipeline (lexer+parser+semantic+codegen)."""

import pytest
from compiler.pipeline import NLToSQLPipeline


@pytest.fixture
def pipeline():
    return NLToSQLPipeline()


class TestCompilationPipeline:
    def test_compile_count(self, pipeline):
        result = pipeline.compile_safe("combien de capteurs")
        assert result["success"]
        assert "COUNT" in result["sql"].upper()

    def test_compile_count_where(self, pipeline):
        result = pipeline.compile_safe("combien de capteurs sont hors service")
        # Should compile even if 'sont' is stop word
        assert result["success"]
        assert list(result["params"].values()) == ["HORS_SERVICE"]

    def test_compile_show_all(self, pipeline):
        result = pipeline.compile_safe("affiche capteurs")
        assert result["success"]
        sql = result["sql"].upper()
        assert "SELECT" in sql
        assert "CAPTEURS" in sql

    def test_compile_where_gt(self, pipeline):
        result = pipeline.compile_safe("quels citoyens ont score > 80")
        assert result["success"]
        sql = result["sql"]
        assert ">" in sql
        # Value is parameterized (:p1); check params dict instead
        assert result["params"] and list(result["params"].values())[0] == 80.0

    def test_compile_orderby_limit(self, pipeline):
        # "les 5 zones" — 'polluées' is not a DB column, but LIMIT should be emitted
        result = pipeline.compile_safe("affiche 5 zones")
        assert result["success"]
        sql = result["sql"].upper()
        assert "LIMIT" in sql or "5" in sql

    def test_compile_avg(self, pipeline):
        result = pipeline.compile_safe("moyenne pm25 des mesures")
        assert result["success"]
        assert "AVG" in result["sql"].upper()

    def test_compile_cross_table_avg_join(self, pipeline):
        result = pipeline.compile_safe("moyenne pm25 des capteurs actifs")
        assert result["success"]
        sql = result["sql"].upper()
        assert "JOIN MESURES" in sql
        assert list(result["params"].values()) == ["ACTIF"]

    def test_compile_interventions_en_cours(self, pipeline):
        result = pipeline.compile_safe("quelles interventions sont en cours")
        assert result["success"]
        assert "!=" in result["sql"]
        assert list(result["params"].values()) == ["TERMINÉ"]

    def test_compile_superlative_adds_limit_one(self, pipeline):
        result = pipeline.compile_safe("donne-moi le trajet le plus économique en CO2")
        assert result["success"]
        assert "LIMIT 1" in result["sql"].upper()

    def test_compile_top_pollution_filters_null_measures(self, pipeline):
        result = pipeline.compile_safe("affiche les 5 zones les plus polluées")
        assert result["success"]
        assert "MESURES.PM25 IS NOT NULL" in result["sql"].upper()

    def test_description_always_present(self, pipeline):
        result = pipeline.compile_safe("affiche interventions")
        assert result["success"]
        assert result["description"]

    def test_ast_structure(self, pipeline):
        result = pipeline.compile_safe("affiche capteurs")
        assert result["success"]
        assert result["ast"]["type"] == "QueryNode"

    def test_unknown_entity_error(self, pipeline):
        result = pipeline.compile_safe("affiche pizzas")
        assert not result["success"]
        assert result["error"] is not None

    def test_unknown_column_error(self, pipeline):
        result = pipeline.compile_safe("affiche capteurs dont pm99 > 50")
        assert not result["success"]
        assert "pm99" in result["error"] or "inconnue" in result["error"]
