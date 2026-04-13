"""
InterventionWorkflowFSM

States: DEMANDE → TECH1_ASSIGNÉ → TECH2_VALIDE → IA_VALIDE → TERMINÉ

The IA_VALIDE transition uses an AI guard that calls the AI action advisor.
The guard result is stored in interventions.ai_validation (JSONB).
"""

from __future__ import annotations
from typing import Callable
from fsm.base import StateMachine, Transition


def make_ai_guard(ai_advisor_fn: Callable[[dict], dict]) -> Callable[[dict], bool]:
    """
    Factory: returns a guard callable that:
      1. Calls ai_advisor_fn(context) to get {"approved": bool, "confidence": float, "reason": str}
      2. Stores the result in context["ai_validation"] for persistence
      3. Returns approved bool
    """
    def guard(ctx: dict) -> bool:
        try:
            result = ai_advisor_fn(ctx)
            ctx["ai_validation"] = result
            return bool(result.get("approved", False))
        except Exception as e:
            ctx["ai_validation"] = {"approved": False, "confidence": 0.0,
                                    "reason": f"Erreur IA: {e}"}
            return False
    return guard


class InterventionWorkflowFSM(StateMachine):

    states = ["DEMANDE", "TECH1_ASSIGNÉ", "TECH2_VALIDE", "IA_VALIDE", "TERMINÉ"]
    initial_state = "DEMANDE"

    def __init__(self, ai_advisor_fn: Callable[[dict], dict] | None = None):
        """
        Args:
            ai_advisor_fn: Optional callable (context → dict with 'approved' key).
                           If None, AI guard always returns True (bypass mode for testing).
        """
        self._ai_advisor_fn = ai_advisor_fn
        self.transitions = self._build_transitions()

    def _build_transitions(self) -> list[Transition]:
        ai_guard = make_ai_guard(self._ai_advisor_fn) if self._ai_advisor_fn else None

        return [
            Transition(
                source="DEMANDE",
                event="assignation_tech1",
                target="TECH1_ASSIGNÉ",
                guard=lambda ctx: bool(ctx.get("tech1_id")),
            ),
            Transition(
                source="TECH1_ASSIGNÉ",
                event="validation_tech2",
                target="TECH2_VALIDE",
                guard=lambda ctx: bool(ctx.get("tech2_id") and ctx.get("rapport_tech1")),
            ),
            Transition(
                source="TECH2_VALIDE",
                event="validation_ia",
                target="IA_VALIDE",
                guard=ai_guard,
            ),
            Transition(
                source="IA_VALIDE",
                event="clôture",
                target="TERMINÉ",
            ),
        ]

    FINAL_STATES = {"TERMINÉ"}
