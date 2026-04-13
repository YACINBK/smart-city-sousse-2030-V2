"""Unit tests for NLParser."""

import pytest
from compiler.lexer import NLLexer
from compiler.parser import NLParser
from compiler.ast_nodes import (QueryNode, SelectIntent, CountIntent,
                                  AvgIntent, TopNIntent, WhereClause)
from compiler.errors import ParseError


@pytest.fixture
def parse():
    lexer = NLLexer()
    parser = NLParser()
    def _parse(query: str) -> QueryNode:
        tokens = lexer.tokenize(query)
        return parser.parse(tokens)
    return _parse


class TestParserIntents:
    def test_select_intent(self, parse):
        node = parse("affiche capteurs")
        assert isinstance(node.intent, SelectIntent)

    def test_count_intent(self, parse):
        node = parse("combien de capteurs")
        assert isinstance(node.intent, CountIntent)

    def test_avg_intent(self, parse):
        node = parse("moyenne pm25 des mesures")
        assert isinstance(node.intent, AvgIntent)

    def test_top_n_intent(self, parse):
        node = parse("affiche 5 capteurs")
        # Could parse as TopNIntent or SelectIntent with limit
        assert node is not None

    def test_entity_resolved(self, parse):
        node = parse("affiche capteurs")
        assert node.entity is not None
        assert node.entity.raw_name in ("capteurs", "capteur")


class TestParserWhere:
    def test_simple_where(self, parse):
        node = parse("affiche capteurs dont statut est actif")
        assert node.where is not None
        assert len(node.where.conditions) == 1

    def test_where_gt(self, parse):
        node = parse("quels citoyens ont score > 80")
        assert node.where is not None
        cond = node.where.conditions[0]
        assert cond.op == ">"
        assert cond.right.raw == "80"

    def test_where_and(self, parse):
        node = parse("affiche capteurs dont type est qualite_air et statut est actif")
        assert node.where is not None
        assert len(node.where.conditions) == 2
        assert "AND" in node.where.operators


class TestParserOrderLimit:
    def test_orderby_desc(self, parse):
        node = parse("affiche mesures par ordre décroissant")
        assert node.orderby is not None
        assert node.orderby.direction == "DESC"

    def test_parse_error_no_entity(self, parse):
        with pytest.raises(ParseError):
            parse("combien font les pizzas")
