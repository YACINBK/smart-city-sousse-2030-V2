"""
FSMStateRepository — reads and writes FSM state to the database.

Tables used:
  - fsm_states (entity_type, entity_id) → current state
  - fsm_history                         → append-only transition log
"""

from __future__ import annotations
from datetime import datetime

from database.connection import execute_query


class FSMStateRepository:

    def get_state(self, entity_type: str, entity_id: int) -> str | None:
        rows = execute_query(
            "SELECT state FROM fsm_states WHERE entity_type=:et AND entity_id=:id",
            {"et": entity_type, "id": entity_id},
        )
        return rows[0]["state"] if rows else None

    def set_state(self, entity_type: str, entity_id: int, state: str) -> None:
        execute_query(
            """INSERT INTO fsm_states (entity_type, entity_id, state, updated_at)
               VALUES (:et, :id, :state, NOW())
               ON CONFLICT (entity_type, entity_id)
               DO UPDATE SET state=EXCLUDED.state, updated_at=NOW()""",
            {"et": entity_type, "id": entity_id, "state": state},
        )

    def record_transition(
        self,
        entity_type: str,
        entity_id: int,
        from_state: str | None,
        event: str,
        to_state: str,
        triggered_by: str = "system",
    ) -> None:
        execute_query(
            """INSERT INTO fsm_history
               (entity_type, entity_id, from_state, event, to_state, triggered_by)
               VALUES (:et, :id, :from_s, :event, :to_s, :by)""",
            {
                "et": entity_type, "id": entity_id,
                "from_s": from_state, "event": event,
                "to_s": to_state, "by": triggered_by,
            },
        )

    def get_history(
        self, entity_type: str, entity_id: int, limit: int = 50
    ) -> list[dict]:
        return execute_query(
            """SELECT from_state, event, to_state, triggered_at, triggered_by
               FROM fsm_history
               WHERE entity_type=:et AND entity_id=:id
               ORDER BY triggered_at ASC
               LIMIT :limit""",
            {"et": entity_type, "id": entity_id, "limit": limit},
        )

    def get_all_states(self, entity_type: str) -> list[dict]:
        return execute_query(
            "SELECT entity_id, state, updated_at FROM fsm_states WHERE entity_type=:et",
            {"et": entity_type},
        )
