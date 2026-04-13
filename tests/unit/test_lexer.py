"""Unit tests for NLLexer."""

import pytest
from compiler.lexer import NLLexer
from compiler.tokens import TokenType
from compiler.errors import LexerError


@pytest.fixture
def lexer():
    return NLLexer()


def token_types(tokens):
    return [t.type for t in tokens if t.type != TokenType.EOF]


class TestLexerBasic:
    def test_empty_query_raises(self, lexer):
        with pytest.raises(LexerError):
            lexer.tokenize("")

    def test_intent_show_variants(self, lexer):
        for word in ["affiche", "montre", "donne", "liste"]:
            tokens = lexer.tokenize(f"{word} capteurs")
            assert tokens[0].type == TokenType.INTENT_SHOW

    def test_intent_count(self, lexer):
        tokens = lexer.tokenize("combien de capteurs")
        assert TokenType.INTENT_COUNT in token_types(tokens)

    def test_entity_recognition(self, lexer):
        tokens = lexer.tokenize("affiche capteurs")
        types = token_types(tokens)
        assert TokenType.ENTITY in types

    def test_number_literal(self, lexer):
        tokens = lexer.tokenize("affiche 5 capteurs")
        nums = [t for t in tokens if t.type == TokenType.NUMBER]
        assert nums and nums[0].value == "5"

    def test_comparator_gt(self, lexer):
        tokens = lexer.tokenize("capteurs dont score > 80")
        cmp_tokens = [t for t in tokens if t.type == TokenType.CMP_GT]
        assert cmp_tokens

    def test_phrase_order_desc(self, lexer):
        tokens = lexer.tokenize("affiche capteurs par ordre décroissant")
        types = token_types(tokens)
        assert TokenType.KW_ORDER_DESC in types

    def test_stop_words_removed(self, lexer):
        tokens = lexer.tokenize("affiche les capteurs")
        # 'les' is a stop word → should not appear
        values = [t.value for t in tokens]
        assert "les" not in values

    def test_accented_keywords(self, lexer):
        tokens = lexer.tokenize("affiche capteurs où statut est actif")
        types = token_types(tokens)
        assert TokenType.KW_WHERE in types

    def test_eof_always_present(self, lexer):
        tokens = lexer.tokenize("affiche capteurs")
        assert tokens[-1].type == TokenType.EOF
