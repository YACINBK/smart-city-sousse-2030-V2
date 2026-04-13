"""
DBContextBuilder — fetches aggregated statistics from the DB and formats
them as markdown tables for injection into LLM prompt templates.
"""

from __future__ import annotations
from datetime import date

from database.connection import execute_query


class DBContextBuilder:

    def air_quality_summary(self, start: date, end: date) -> str:
        rows = execute_query(
            """
            SELECT
                z.nom AS zone,
                ROUND(AVG(m.pm25)::numeric, 2) AS avg_pm25,
                ROUND(AVG(m.pm10)::numeric, 2) AS avg_pm10,
                ROUND(MAX(m.pm25)::numeric, 2) AS max_pm25,
                COUNT(m.id) AS nb_mesures
            FROM mesures m
            JOIN capteurs c ON c.id = m.capteur_id
            LEFT JOIN zones z ON z.id = c.zone_id
            WHERE m.mesure_at BETWEEN :start AND :end
              AND m.pm25 IS NOT NULL
            GROUP BY z.nom
            ORDER BY avg_pm25 DESC
            LIMIT 15
            """,
            {"start": str(start), "end": str(end)},
        )
        if not rows:
            return "Aucune mesure disponible pour cette période."
        lines = ["| Zone | PM2.5 moy. | PM10 moy. | PM2.5 max | Mesures |",
                 "|------|-----------|----------|----------|---------|"]
        for r in rows:
            lines.append(f"| {r['zone']} | {r['avg_pm25']} | {r['avg_pm10']} "
                         f"| {r['max_pm25']} | {r['nb_mesures']} |")
        return "\n".join(lines)

    def intervention_summary(self, start: date, end: date) -> str:
        rows = execute_query(
            """
            SELECT
                statut,
                COUNT(*) AS total,
                ROUND(AVG(EXTRACT(EPOCH FROM (COALESCE(completed_at, NOW()) - created_at))/3600)::numeric, 1) AS duree_moy_h
            FROM interventions
            WHERE created_at BETWEEN :start AND :end
            GROUP BY statut
            ORDER BY total DESC
            """,
            {"start": str(start), "end": str(end)},
        )
        if not rows:
            return "Aucune intervention pour cette période."
        lines = ["| Statut | Total | Durée moy. (h) |",
                 "|--------|-------|----------------|"]
        for r in rows:
            lines.append(f"| {r['statut']} | {r['total']} | {r['duree_moy_h']} |")
        return "\n".join(lines)

    def sensor_status_summary(self) -> str:
        rows = execute_query(
            """
            SELECT statut, COUNT(*) AS total
            FROM capteurs
            GROUP BY statut
            ORDER BY total DESC
            """
        )
        if not rows:
            return "Aucun capteur enregistré."
        lines = ["| Statut | Nombre |", "|--------|--------|"]
        for r in rows:
            lines.append(f"| {r['statut']} | {r['total']} |")
        return "\n".join(lines)

    def quick_stats(self) -> dict:
        """Returns scalar stats for the GENERAL_RECOMMENDATIONS prompt."""
        def scalar(sql, params=None):
            rows = execute_query(sql, params)
            if rows:
                return list(rows[0].values())[0]
            return 0

        return {
            "hors_service_count": scalar(
                "SELECT COUNT(*) FROM capteurs WHERE statut='HORS_SERVICE'"
            ),
            "pending_interventions": scalar(
                "SELECT COUNT(*) FROM interventions WHERE statut != 'TERMINÉ'"
            ),
            "critical_alerts": scalar(
                "SELECT COUNT(*) FROM alertes WHERE severity='CRITICAL' AND resolved=FALSE"
            ),
            "critical_zones": scalar(
                "SELECT COUNT(DISTINCT z.nom) FROM mesures m "
                "JOIN capteurs c ON c.id=m.capteur_id "
                "JOIN zones z ON z.id=c.zone_id "
                "WHERE m.pm25 > 35 AND m.mesure_at > NOW() - INTERVAL '24 hours'"
            ),
            "vehicles_breakdown": scalar(
                "SELECT COUNT(*) FROM vehicules WHERE statut='EN_PANNE'"
            ),
        }
