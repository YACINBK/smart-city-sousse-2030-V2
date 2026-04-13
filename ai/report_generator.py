"""
ReportGenerator — produces textual reports by combining DB context with LLM generation.
"""

from __future__ import annotations
from datetime import date

from ai.client import LLMClient, get_llm_client
from ai.context_builder import DBContextBuilder
from ai.prompts.report_templates import (
    AIR_QUALITY_REPORT,
    INTERVENTION_REPORT,
    SENSOR_STATUS_REPORT,
    GENERAL_RECOMMENDATIONS,
)


REPORT_TYPES = {
    "qualite_air": "Qualité de l'Air",
    "interventions": "Interventions",
    "capteurs": "État des Capteurs",
    "recommandations": "Recommandations Prioritaires",
}


class ReportGenerator:

    def __init__(self, client: LLMClient | None = None):
        self._client = client or get_llm_client()
        self._ctx = DBContextBuilder()

    def generate(
        self,
        report_type: str,
        start: date | None = None,
        end: date | None = None,
    ) -> str:
        """
        Generate a report for the given type and date range.

        Args:
            report_type: One of the keys in REPORT_TYPES.
            start, end: Date range for the report.

        Returns:
            Markdown-formatted report string.
        """
        from datetime import date as dt
        start = start or dt.today().replace(day=1)
        end = end or dt.today()
        period = f"{start.strftime('%d/%m/%Y')} — {end.strftime('%d/%m/%Y')}"

        if report_type == "qualite_air":
            data = self._ctx.air_quality_summary(start, end)
            prompt = AIR_QUALITY_REPORT.format(period=period, data_summary=data)

        elif report_type == "interventions":
            data = self._ctx.intervention_summary(start, end)
            prompt = INTERVENTION_REPORT.format(period=period, data_summary=data)

        elif report_type == "capteurs":
            data = self._ctx.sensor_status_summary()
            prompt = SENSOR_STATUS_REPORT.format(period=period, data_summary=data)

        elif report_type == "recommandations":
            stats = self._ctx.quick_stats()
            prompt = GENERAL_RECOMMENDATIONS.format(**stats)

        else:
            return f"Type de rapport inconnu : '{report_type}'. Choisissez parmi : {list(REPORT_TYPES.keys())}"

        return self._client.complete(prompt, max_tokens=2000)

    def explain_sql(self, sql: str) -> str:
        """Translate a generated SQL query back to natural French (confirmation feature)."""
        prompt = (
            f"Traduis cette requête SQL en français naturel en une phrase simple, "
            f"comme si tu expliquais à un non-technicien ce qu'elle fait. "
            f"Commence par 'J'ai compris : vous voulez...'.\n\n```sql\n{sql}\n```"
        )
        return self._client.complete(prompt, max_tokens=150)
