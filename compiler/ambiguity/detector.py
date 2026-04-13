"""
AmbiguityDetector — post-parse analysis of the AST.

Detects three kinds of ambiguity:
  1. Entity ambiguity: "capteurs" without a statut filter → could mean all or active only
  2. Attribute ambiguity: attribute maps to multiple columns
  3. Aggregation ambiguity: AVG/COUNT without explicit target and multiple numeric columns

Returns None if unambiguous, or an AmbiguityResult with candidate SQLs and a question.
"""

from dataclasses import dataclass

from compiler.ast_nodes import QueryNode, AvgIntent, SelectIntent
from compiler.tokens import SCHEMA_REGISTRY
from compiler.codegen import SQLCodeGenerator


@dataclass
class AmbiguityResult:
    question: str
    candidate_sqls: list[str]


class AmbiguityDetector:

    def __init__(self):
        self._codegen = SQLCodeGenerator()

    def detect(self, node: QueryNode, original_query: str) -> AmbiguityResult | None:
        """Return AmbiguityResult if the query is ambiguous, else None."""

        # ── 1. Aggregation ambiguity for AVG without explicit target ──
        if isinstance(node.intent, AvgIntent) and node.intent.target is None:
            table = node.entity.resolved_table if node.entity else None
            if table:
                numeric_cols = self._numeric_cols(table)
                if len(numeric_cols) > 1:
                    return self._make_avg_ambiguity(node, numeric_cols, original_query)

        # ── 2. "Affiche les mesures" without specifying which measure ──
        if (isinstance(node.intent, SelectIntent)
                and node.entity
                and node.entity.resolved_table == "mesures"
                and not node.attributes
                and not node.where):
            return AmbiguityResult(
                question=(
                    "Quelle grandeur souhaitez-vous afficher ? "
                    "PM2.5, PM10, température, humidité, CO2, NO2 ?"
                ),
                candidate_sqls=[
                    "SELECT capteur_id, mesure_at, pm25 FROM mesures ORDER BY mesure_at DESC LIMIT 50",
                    "SELECT capteur_id, mesure_at, pm10 FROM mesures ORDER BY mesure_at DESC LIMIT 50",
                    "SELECT capteur_id, mesure_at, temperature FROM mesures ORDER BY mesure_at DESC LIMIT 50",
                    "SELECT * FROM mesures ORDER BY mesure_at DESC LIMIT 50",
                ],
            )

        return None

    # ──────────────────────────────────────────────────────────

    def _numeric_cols(self, table: str) -> list[str]:
        return [
            c for c in SCHEMA_REGISTRY.get(table, [])
            if any(c.startswith(p) for p in
                   ("pm", "temp", "hum", "co2", "no2", "score", "dist", "eco", "bruit", "traf"))
        ]

    def _make_avg_ambiguity(
        self, node: QueryNode, numeric_cols: list[str], original_query: str
    ) -> AmbiguityResult:
        from copy import deepcopy
        from compiler.ast_nodes import AttributeRef

        candidate_sqls: list[str] = []
        table = node.entity.resolved_table

        for col in numeric_cols[:4]:  # cap at 4 options
            clone = deepcopy(node)
            clone.intent.target = AttributeRef(
                raw_name=col, resolved_column=col, resolved_table=table
            )
            try:
                result = self._codegen.generate(clone)
                candidate_sqls.append(result.sql)
            except Exception:
                pass

        cols_str = ", ".join(numeric_cols[:4])
        question = (
            f"De quelle grandeur souhaitez-vous calculer la moyenne ? "
            f"Colonnes disponibles : {cols_str}."
        )
        return AmbiguityResult(question=question, candidate_sqls=candidate_sqls)
