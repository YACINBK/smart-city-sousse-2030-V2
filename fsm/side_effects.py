"""
SideEffectRegistry — maps action names to handler callables.

Handlers receive a context dict and may perform DB writes, scheduling,
or external notifications. All handlers are registered at startup.
"""

from __future__ import annotations
from typing import Callable
from datetime import datetime


class SideEffectRegistry:
    """
    Singleton-style registry for FSM side-effect handlers.
    Each automaton action name maps to one or more callables.
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._log: list[dict] = []  # in-memory audit log for testing

    def register(self, action_name: str, handler: Callable) -> None:
        self._handlers.setdefault(action_name, []).append(handler)

    def run(self, action_name: str, context: dict) -> list:
        results = []
        for handler in self._handlers.get(action_name, []):
            try:
                result = handler(context)
                results.append(result)
            except Exception as exc:
                results.append({"error": str(exc)})
        self._log.append({
            "action": action_name,
            "context": context,
            "at": datetime.now().isoformat(),
            "results": results,
        })
        return results

    def get_log(self) -> list[dict]:
        return list(self._log)


# ──────────────────────────────────────────────────────────────
# Default handlers (wired up in database-connected environment)
# ──────────────────────────────────────────────────────────────

def make_db_handlers(db_execute_fn):
    """
    Factory: returns a dict of {action_name: handler} that use db_execute_fn
    to persist side effects. Pass database.connection.execute_query.
    """

    def log_activation(ctx: dict):
        sensor_id = ctx.get("entity_id")
        db_execute_fn(
            "UPDATE capteurs SET statut='ACTIF', date_installation=NOW() WHERE id=:id",
            {"id": sensor_id}
        )

    def create_alert(ctx: dict):
        db_execute_fn(
            """INSERT INTO alertes (type, entity_type, entity_id, message, severity)
               VALUES ('anomalie_détectée', 'capteur', :id, :msg, 'WARNING')""",
            {"id": ctx.get("entity_id"),
             "msg": f"Anomalie détectée sur capteur {ctx.get('entity_id')}"}
        )

    def notify_critical(ctx: dict):
        db_execute_fn(
            """INSERT INTO alertes (type, entity_type, entity_id, message, severity)
               VALUES ('capteur_critique', 'capteur', :id, :msg, 'CRITICAL')""",
            {"id": ctx.get("entity_id"),
             "msg": f"Capteur {ctx.get('entity_id')} hors service — surveillance requise"}
        )

    def close_alert(ctx: dict):
        db_execute_fn(
            """UPDATE alertes SET resolved=TRUE, resolved_at=NOW()
               WHERE entity_type='capteur' AND entity_id=:id AND resolved=FALSE""",
            {"id": ctx.get("entity_id")}
        )

    def update_intervention_metrics(ctx: dict):
        db_execute_fn(
            "UPDATE interventions SET completed_at=NOW() WHERE id=:id",
            {"id": ctx.get("entity_id")}
        )

    def update_capteur_statut(ctx: dict):
        """Sync capteurs.statut with the FSM state."""
        db_execute_fn(
            "UPDATE capteurs SET statut=:statut WHERE id=:id",
            {"statut": ctx.get("to_state", "ACTIF"), "id": ctx.get("entity_id")}
        )

    return {
        "log_activation": log_activation,
        "create_alert": create_alert,
        "notify_critical": notify_critical,
        "close_alert": close_alert,
        "close_maintenance": close_alert,
        "update_metrics": update_intervention_metrics,
        "sync_capteur_statut": update_capteur_statut,
    }
