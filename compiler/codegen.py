"""
SQLCodeGenerator — single-pass tree walk over a semantically-analyzed
QueryNode, emitting a parameterized SQL string + parameter dict.

Returns a CompileResult namedtuple with:
  - sql: str  (the complete SQL query)
  - params: dict  (named parameters for safe DB execution)
  - description: str  (French human-readable explanation of what was generated)
"""

from dataclasses import dataclass
from compiler.ast_nodes import (
    QueryNode, SelectIntent, CountIntent, AvgIntent, TopNIntent,
    AttributeRef,
)
from compiler.errors import SemanticError
from compiler.tokens import ATTRIBUTE_COLUMN_MAP


@dataclass
class CompileResult:
    sql: str
    params: dict
    description: str


class SQLCodeGenerator:

    def generate(self, node: QueryNode) -> CompileResult:
        table = node.entity.resolved_table if node.entity else None
        if table is None and not isinstance(node.intent, CountIntent):
            raise SemanticError("Impossible de générer le SQL : entité manquante.", pos=0)

        params: dict = {}
        param_idx = [0]  # mutable counter

        def next_param(value) -> str:
            param_idx[0] += 1
            key = f"p{param_idx[0]}"
            params[key] = value
            return f":{key}"

        # ── Cross-table aggregation shortcut ─────────────────
        meta = getattr(node, "meta", None) or {}
        if meta.get("avg_join"):
            return self._generate_cross_table_avg(node, table, meta, next_param, params)
        if meta.get("cross_join"):
            return self._generate_cross_table(node, table, meta, next_param, params)

        # ── SELECT clause ────────────────────────────────────
        intent = node.intent

        if isinstance(intent, CountIntent):
            if intent.target and intent.target.resolved_column:
                col = self._col(intent.target)
                select_clause = f"SELECT COUNT({col})"
            else:
                select_clause = "SELECT COUNT(*)"

        elif isinstance(intent, AvgIntent):
            if intent.target and intent.target.resolved_column:
                col = self._col(intent.target)
                select_clause = f"SELECT AVG({col}) AS moyenne_{intent.target.resolved_column}"
            else:
                raise SemanticError("AVG requiert une colonne cible.", pos=0)

        elif isinstance(intent, (SelectIntent, TopNIntent)):
            if node.attributes:
                cols = ", ".join(self._col(a) for a in node.attributes)
                # If groupby is present and aggregation is implied, add COUNT
                if node.groupby:
                    group_cols = ", ".join(self._col(a) for a in node.groupby.attributes)
                    select_clause = f"SELECT {group_cols}, COUNT(*) AS total"
                else:
                    select_clause = f"SELECT {cols}"
            elif node.groupby:
                group_cols = ", ".join(self._col(a) for a in node.groupby.attributes)
                select_clause = f"SELECT {group_cols}, COUNT(*) AS total"
            else:
                select_clause = "SELECT *"
        else:
            select_clause = "SELECT *"

        # ── FROM clause ──────────────────────────────────────
        from_clause = f"FROM {table}" if table else ""

        # ── WHERE clause ─────────────────────────────────────
        where_parts: list[str] = []
        if node.where:
            for i, cond in enumerate(node.where.conditions):
                col = self._col(cond.left)
                val = cond.right.coerced if cond.right.coerced is not None else cond.right.raw

                # Handle NULL checks
                if str(val).lower() in {"null", "nul", "aucun"}:
                    where_parts.append(f"{col} IS NULL")
                else:
                    p = next_param(val)
                    where_parts.append(f"{col} {cond.op} {p}")

                if i < len(node.where.operators):
                    where_parts.append(node.where.operators[i])

        where_clause = f"WHERE {' '.join(where_parts)}" if where_parts else ""

        # ── GROUP BY clause ──────────────────────────────────
        groupby_clause = ""
        if node.groupby:
            group_cols = ", ".join(self._col(a) for a in node.groupby.attributes)
            groupby_clause = f"GROUP BY {group_cols}"

        # ── ORDER BY clause ──────────────────────────────────
        orderby_clause = ""
        if node.orderby:
            if node.orderby.attribute:
                order_col = self._col(node.orderby.attribute)
            elif isinstance(intent, AvgIntent) and intent.target:
                order_col = f"AVG({self._col(intent.target)})"
            elif node.groupby:
                # Default: order by the aggregate
                order_col = "COUNT(*)"
            else:
                order_col = "1"
            orderby_clause = f"ORDER BY {order_col} {node.orderby.direction}"
        elif isinstance(intent, TopNIntent):
            # TopN without explicit order → order by first numeric or COUNT desc
            if node.groupby:
                orderby_clause = "ORDER BY COUNT(*) DESC"
            elif node.attributes:
                orderby_clause = f"ORDER BY {self._col(node.attributes[0])} DESC"

        # ── LIMIT clause ─────────────────────────────────────
        limit_clause = ""
        if node.limit:
            limit_clause = f"LIMIT {node.limit.n}"
        elif isinstance(intent, TopNIntent):
            limit_clause = f"LIMIT {intent.n}"

        # ── Assemble ─────────────────────────────────────────
        parts = [p for p in [select_clause, from_clause, where_clause,
                              groupby_clause, orderby_clause, limit_clause] if p]
        sql = "\n".join(parts)

        description = self._describe(node, table)
        return CompileResult(sql=sql, params=params, description=description)

    # ──────────────────────────────────────────────────────────

    def _generate_cross_table(
        self, node: QueryNode, entity_table: str, meta: dict, next_param, params: dict
    ) -> "CompileResult":
        """
        Generate SQL for cross-table aggregation, e.g.:
          "les 5 zones les plus polluées"
          → SELECT zones.nom, AVG(mesures.pm25) AS avg_val
            FROM zones
            JOIN capteurs _c ON _c.zone_id = zones.id
            JOIN mesures ON mesures.capteur_id = _c.id
            GROUP BY zones.nom
            ORDER BY AVG(mesures.pm25) DESC
            LIMIT 5
        """
        agg_col   = ATTRIBUTE_COLUMN_MAP.get(meta["agg_col"], meta["agg_col"])
        agg_table = meta["agg_table"]
        join_sql  = meta["cross_join"]
        group_col = meta.get("group_col", "nom")
        direction = node.orderby.direction if node.orderby else "DESC"

        label = f"{entity_table}.{group_col}"
        agg_expr = f"AVG({agg_table}.{agg_col})"

        select_clause  = f"SELECT {label}, {agg_expr} AS avg_{agg_col}"
        from_clause    = f"FROM {entity_table}"
        join_clause    = join_sql
        groupby_clause = f"GROUP BY {label}"
        orderby_clause = f"ORDER BY {agg_expr} {direction}"
        limit_clause   = ""

        if node.limit:
            limit_clause = f"LIMIT {node.limit.n}"
        elif isinstance(node.intent, TopNIntent):
            limit_clause = f"LIMIT {node.intent.n}"

        where_parts: list[str] = []
        where_parts.append(f"{agg_table}.{agg_col} IS NOT NULL")
        if node.where:
            for i, cond in enumerate(node.where.conditions):
                col = self._col(cond.left)
                val = cond.right.coerced if cond.right.coerced is not None else cond.right.raw
                if str(val).lower() in {"null", "nul", "aucun"}:
                    where_parts.append(f"{col} IS NULL")
                else:
                    p = next_param(val)
                    where_parts.append(f"{col} {cond.op} {p}")
                if i < len(node.where.operators):
                    where_parts.append(node.where.operators[i])
        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        parts = [p for p in [select_clause, from_clause, join_clause,
                              where_clause, groupby_clause, orderby_clause, limit_clause] if p]
        sql = "\n".join(parts)
        description = (
            f"Afficher les {node.intent.n if isinstance(node.intent, TopNIntent) else ''} "
            f"{entity_table} triés par {agg_col} moyen ({direction})."
        ).strip()
        return CompileResult(sql=sql, params=params, description=description)

    def _generate_cross_table_avg(
        self, node: QueryNode, entity_table: str, meta: dict, next_param, params: dict
    ) -> "CompileResult":
        intent = node.intent
        target = intent.target
        agg_col = self._col(target)

        select_clause = f"SELECT AVG({agg_col}) AS moyenne_{target.resolved_column}"
        from_clause = f"FROM {entity_table}"
        join_clause = meta["avg_join"]

        where_parts: list[str] = []
        if node.where:
            for i, cond in enumerate(node.where.conditions):
                col = self._col(cond.left)
                val = cond.right.coerced if cond.right.coerced is not None else cond.right.raw
                if str(val).lower() in {"null", "nul", "aucun"}:
                    where_parts.append(f"{col} IS NULL")
                else:
                    p = next_param(val)
                    where_parts.append(f"{col} {cond.op} {p}")
                if i < len(node.where.operators):
                    where_parts.append(node.where.operators[i])
        where_clause = f"WHERE {' '.join(where_parts)}" if where_parts else ""

        parts = [p for p in [select_clause, from_clause, join_clause, where_clause] if p]
        sql = "\n".join(parts)
        description = self._describe(node, entity_table)
        return CompileResult(sql=sql, params=params, description=description)

    def _col(self, attr: AttributeRef) -> str:
        if attr.resolved_table and attr.resolved_column:
            return f"{attr.resolved_table}.{attr.resolved_column}"
        if attr.resolved_column:
            return attr.resolved_column
        return attr.raw_name

    def _describe(self, node: QueryNode, table: str | None) -> str:
        intent = node.intent
        entity_str = table or "données"

        if isinstance(intent, CountIntent):
            base = f"Compter le nombre d'enregistrements dans '{entity_str}'"
        elif isinstance(intent, AvgIntent):
            col = intent.target.resolved_column if intent.target else "?"
            base = f"Calculer la moyenne de '{col}' dans '{entity_str}'"
        elif isinstance(intent, TopNIntent):
            base = f"Afficher les {intent.n} premiers résultats de '{entity_str}'"
        else:
            base = f"Afficher les données de '{entity_str}'"

        if node.where:
            conditions_str = ", ".join(
                f"{c.left.resolved_column or c.left.raw_name} {c.op} {c.right.raw}"
                for c in node.where.conditions
            )
            base += f" où {conditions_str}"

        if node.groupby:
            cols = ", ".join(a.resolved_column or a.raw_name for a in node.groupby.attributes)
            base += f", groupés par {cols}"

        if node.orderby:
            dir_fr = "décroissant" if node.orderby.direction == "DESC" else "croissant"
            col = node.orderby.attribute.resolved_column if node.orderby.attribute else "résultat"
            base += f", triés par {col} {dir_fr}"

        if node.limit:
            base += f", limité à {node.limit.n} résultats"

        return base + "."
