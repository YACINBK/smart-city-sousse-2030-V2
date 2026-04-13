"""
NLParser — recursive-descent parser for the French NL query grammar.

Grammar (EBNF):
  query         ::= intent_clause entity_clause
                    [ where_clause ] [ groupby_clause ] [ orderby_clause ] [ limit_clause ] EOF
  intent_clause ::= INTENT_SHOW | INTENT_COUNT | INTENT_AVG [attribute_ref] | INTENT_TOP NUMBER
  entity_clause ::= ENTITY [ attribute_list ]
  attribute_list::= attribute_ref { ',' attribute_ref } | '*'
  where_clause  ::= KW_WHERE condition { (KW_AND | KW_OR) condition }
  condition     ::= attribute_ref comparator value
  groupby_clause::= KW_GROUPBY attribute_ref { ',' attribute_ref }
  orderby_clause::= (KW_ORDER_ASC | KW_ORDER_DESC) attribute_ref
  limit_clause  ::= KW_LIMIT NUMBER | INTENT_TOP NUMBER
"""

from compiler.tokens import Token, TokenType
from compiler.ast_nodes import (
    QueryNode, EntityRef, AttributeRef, ValueNode,
    SelectIntent, CountIntent, AvgIntent, TopNIntent,
    WhereClause, ConditionNode, GroupByClause, OrderByClause, LimitClause,
)
from compiler.errors import ParseError

_COMPARATORS = {
    TokenType.CMP_EQ: "=",
    TokenType.CMP_GT: ">",
    TokenType.CMP_LT: "<",
    TokenType.CMP_GTE: ">=",
    TokenType.CMP_LTE: "<=",
}


class NLParser:
    """Converts a token list (from NLLexer) into a QueryNode AST."""

    def __init__(self):
        self._tokens: list[Token] = []
        self._pos: int = 0

    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────

    def parse(self, tokens: list[Token]) -> QueryNode:
        self._tokens = tokens
        self._pos = 0
        return self._parse_query()

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 1) -> Token | None:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return None

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, *types: TokenType) -> Token:
        tok = self._current()
        if tok.type not in types:
            names = " ou ".join(t.name for t in types)
            raise ParseError(
                f"Erreur syntaxique : attendu {names}, trouvé '{tok.value}' ({tok.type.name}).",
                pos=tok.pos,
            )
        return self._advance()

    def _match(self, *types: TokenType) -> bool:
        return self._current().type in types

    # ──────────────────────────────────────────────────────────
    # Grammar rules
    # ──────────────────────────────────────────────────────────

    def _parse_query(self) -> QueryNode:
        node = QueryNode(pos=self._current().pos)

        node.intent = self._parse_intent()

        # "affiche 5 capteurs..." — NUMBER after SelectIntent means TopN + entity
        if isinstance(node.intent, SelectIntent) and self._match(TokenType.NUMBER):
            n_tok = self._advance()
            node.intent = TopNIntent(n=int(float(n_tok.value)), pos=n_tok.pos)

        # entity is required unless COUNT has a sub-attribute
        if self._match(TokenType.ENTITY):
            node.entity = self._parse_entity_ref()
            node.attributes = self._parse_attribute_list()
        elif not isinstance(node.intent, CountIntent):
            raise ParseError(
                "Erreur syntaxique : entité attendue (ex: capteurs, interventions).",
                pos=self._current().pos,
            )

        if self._match(TokenType.KW_WHERE):
            node.where = self._parse_where()

        if self._match(TokenType.KW_GROUPBY):
            node.groupby = self._parse_groupby()

        if self._match(TokenType.KW_ORDER_ASC, TokenType.KW_ORDER_DESC):
            node.orderby = self._parse_orderby()

        if self._match(TokenType.KW_LIMIT):
            node.limit = self._parse_limit()

        self._expect(TokenType.EOF)
        return node

    def _parse_intent(self) -> SelectIntent | CountIntent | AvgIntent | TopNIntent:
        tok = self._current()

        if tok.type == TokenType.INTENT_SHOW:
            self._advance()
            return SelectIntent(pos=tok.pos)

        if tok.type == TokenType.INTENT_COUNT:
            self._advance()
            return CountIntent(pos=tok.pos)

        if tok.type == TokenType.INTENT_AVG:
            self._advance()
            target = None
            if self._match(TokenType.ATTRIBUTE, TokenType.IDENTIFIER):
                target = self._parse_attribute_ref()
            return AvgIntent(target=target, pos=tok.pos)

        if tok.type == TokenType.INTENT_TOP:
            self._advance()
            n_tok = self._expect(TokenType.NUMBER)
            return TopNIntent(n=int(float(n_tok.value)), pos=tok.pos)

        # Also accept: NUMBER directly as a "top N" intent (e.g., "les 5 zones")
        if tok.type == TokenType.NUMBER:
            n = int(float(tok.value))
            self._advance()
            return TopNIntent(n=n, pos=tok.pos)

        raise ParseError(
            f"Erreur syntaxique : requête doit commencer par une intention "
            f"(affiche, combien, moyenne…), trouvé '{tok.value}'.",
            pos=tok.pos,
        )

    def _parse_entity_ref(self) -> EntityRef:
        tok = self._expect(TokenType.ENTITY)
        return EntityRef(raw_name=tok.value, pos=tok.pos)

    def _parse_attribute_list(self) -> list[AttributeRef]:
        attrs: list[AttributeRef] = []
        if self._match(TokenType.ATTRIBUTE, TokenType.IDENTIFIER):
            attrs.append(self._parse_attribute_ref())
            while self._match(TokenType.ATTRIBUTE, TokenType.IDENTIFIER):
                # Stop if next token looks like a clause keyword
                if self._current().type in {
                    TokenType.KW_WHERE, TokenType.KW_GROUPBY,
                    TokenType.KW_ORDER_ASC, TokenType.KW_ORDER_DESC, TokenType.KW_LIMIT
                }:
                    break
                attrs.append(self._parse_attribute_ref())
        return attrs

    def _parse_attribute_ref(self) -> AttributeRef:
        tok = self._advance()
        return AttributeRef(raw_name=tok.value, pos=tok.pos)

    def _parse_where(self) -> WhereClause:
        pos = self._current().pos
        self._advance()  # consume KW_WHERE
        clause = WhereClause(pos=pos)

        clause.conditions.append(self._parse_condition())

        while self._match(TokenType.KW_AND, TokenType.KW_OR):
            op_tok = self._advance()
            clause.operators.append("AND" if op_tok.type == TokenType.KW_AND else "OR")
            clause.conditions.append(self._parse_condition())

        return clause

    def _parse_condition(self) -> ConditionNode:
        pos = self._current().pos
        left = self._parse_attribute_ref()
        op_tok = self._current()
        if op_tok.type not in _COMPARATORS:
            raise ParseError(
                f"Erreur syntaxique : comparateur attendu (est, >, <, supérieur…), "
                f"trouvé '{op_tok.value}'.",
                pos=op_tok.pos,
            )
        self._advance()
        op = _COMPARATORS[op_tok.type]
        right = self._parse_value()
        return ConditionNode(left=left, op=op, right=right, pos=pos)

    def _parse_value(self) -> ValueNode:
        tok = self._current()
        if tok.type == TokenType.NUMBER:
            self._advance()
            return ValueNode(raw=tok.value, kind="number", pos=tok.pos)
        if tok.type == TokenType.STRING:
            self._advance()
            return ValueNode(raw=tok.value, kind="string", pos=tok.pos)
        if tok.type in {TokenType.IDENTIFIER, TokenType.ATTRIBUTE, TokenType.ENTITY}:
            self._advance()
            return ValueNode(raw=tok.value, kind="identifier", pos=tok.pos)
        raise ParseError(
            f"Erreur syntaxique : valeur attendue, trouvé '{tok.value}'.",
            pos=tok.pos,
        )

    def _parse_groupby(self) -> GroupByClause:
        pos = self._current().pos
        self._advance()  # consume KW_GROUPBY
        clause = GroupByClause(pos=pos)
        clause.attributes.append(self._parse_attribute_ref())
        while self._match(TokenType.ATTRIBUTE, TokenType.IDENTIFIER):
            if self._current().type in {
                TokenType.KW_ORDER_ASC, TokenType.KW_ORDER_DESC, TokenType.KW_LIMIT, TokenType.EOF
            }:
                break
            clause.attributes.append(self._parse_attribute_ref())
        return clause

    def _parse_orderby(self) -> OrderByClause:
        pos = self._current().pos
        direction = "DESC" if self._current().type == TokenType.KW_ORDER_DESC else "ASC"
        self._advance()
        attr = None
        if self._match(TokenType.ATTRIBUTE, TokenType.IDENTIFIER, TokenType.ENTITY):
            attr = self._parse_attribute_ref()
        return OrderByClause(attribute=attr, direction=direction, pos=pos)

    def _parse_limit(self) -> LimitClause:
        pos = self._current().pos
        self._advance()  # consume KW_LIMIT
        n_tok = self._expect(TokenType.NUMBER)
        return LimitClause(n=int(float(n_tok.value)), pos=pos)
