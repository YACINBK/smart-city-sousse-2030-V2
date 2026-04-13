"""
AST node hierarchy for the NL→SQL compiler.

All nodes are @dataclass for easy inspection and JSON serialization.
Nodes carry a `pos` field (character offset in original query) for
accurate error reporting.

Semantic analysis fills in `resolved_*` fields; the parser only sets `raw_*`.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


# ──────────────────────────────────────────────────────────────
# Leaf / reference nodes
# ──────────────────────────────────────────────────────────────

@dataclass
class EntityRef:
    raw_name: str
    resolved_table: Optional[str] = None
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "EntityRef", "raw": self.raw_name, "table": self.resolved_table}


@dataclass
class AttributeRef:
    raw_name: str
    resolved_column: Optional[str] = None
    resolved_table: Optional[str] = None
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "AttributeRef", "raw": self.raw_name,
                "column": self.resolved_column, "table": self.resolved_table}


@dataclass
class ValueNode:
    raw: str
    kind: str           # 'string' | 'number' | 'identifier'
    coerced: Any = None  # filled by SemanticAnalyzer
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "ValueNode", "raw": self.raw, "kind": self.kind, "coerced": self.coerced}


# ──────────────────────────────────────────────────────────────
# Intent nodes
# ──────────────────────────────────────────────────────────────

@dataclass
class SelectIntent:
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "SelectIntent"}


@dataclass
class CountIntent:
    target: Optional[AttributeRef] = None  # None → COUNT(*)
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "CountIntent", "target": self.target.to_dict() if self.target else None}


@dataclass
class AvgIntent:
    target: Optional[AttributeRef] = None
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "AvgIntent", "target": self.target.to_dict() if self.target else None}


@dataclass
class TopNIntent:
    n: int = 10
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "TopNIntent", "n": self.n}


# ──────────────────────────────────────────────────────────────
# Clause nodes
# ──────────────────────────────────────────────────────────────

@dataclass
class ConditionNode:
    left: AttributeRef
    op: str             # '=' | '>' | '<' | '>=' | '<='
    right: ValueNode
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "ConditionNode",
                "left": self.left.to_dict(), "op": self.op, "right": self.right.to_dict()}


@dataclass
class WhereClause:
    conditions: list[ConditionNode] = field(default_factory=list)
    operators: list[str] = field(default_factory=list)  # 'AND' | 'OR' between conditions
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "WhereClause",
                "conditions": [c.to_dict() for c in self.conditions],
                "operators": self.operators}


@dataclass
class GroupByClause:
    attributes: list[AttributeRef] = field(default_factory=list)
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "GroupByClause",
                "attributes": [a.to_dict() for a in self.attributes]}


@dataclass
class OrderByClause:
    attribute: Optional[AttributeRef] = None
    direction: str = "ASC"   # 'ASC' | 'DESC'
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "OrderByClause",
                "attribute": self.attribute.to_dict() if self.attribute else None,
                "direction": self.direction}


@dataclass
class LimitClause:
    n: int = 10
    pos: int = 0

    def to_dict(self) -> dict:
        return {"type": "LimitClause", "n": self.n}


# ──────────────────────────────────────────────────────────────
# Root node
# ──────────────────────────────────────────────────────────────

@dataclass
class QueryNode:
    intent: SelectIntent | CountIntent | AvgIntent | TopNIntent = field(
        default_factory=SelectIntent)
    entity: Optional[EntityRef] = None
    attributes: list[AttributeRef] = field(default_factory=list)
    where: Optional[WhereClause] = None
    groupby: Optional[GroupByClause] = None
    orderby: Optional[OrderByClause] = None
    limit: Optional[LimitClause] = None
    pos: int = 0

    def to_dict(self) -> dict:
        return {
            "type": "QueryNode",
            "intent": self.intent.to_dict(),
            "entity": self.entity.to_dict() if self.entity else None,
            "attributes": [a.to_dict() for a in self.attributes],
            "where": self.where.to_dict() if self.where else None,
            "groupby": self.groupby.to_dict() if self.groupby else None,
            "orderby": self.orderby.to_dict() if self.orderby else None,
            "limit": self.limit.to_dict() if self.limit else None,
        }
