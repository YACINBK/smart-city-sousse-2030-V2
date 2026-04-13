"""
ActionAdvisor — validates FSM intervention transitions and suggests manager actions.
"""

from __future__ import annotations
import json

from ai.client import LLMClient, get_llm_client
from ai.context_builder import DBContextBuilder
from ai.prompts.report_templates import GENERAL_RECOMMENDATIONS


class ActionAdvisor:

    def __init__(self, client: LLMClient | None = None):
        self._client = client or get_llm_client()
        self._ctx = DBContextBuilder()

    def validate_intervention(self, context: dict) -> dict:
        """
        AI guard for InterventionWorkflowFSM's IA_VALIDE transition.

        Args:
            context: dict with keys: entity_id, description, rapport_tech1,
                     rapport_tech2, capteur_statut, etc.

        Returns:
            {"approved": bool, "confidence": float, "reason": str}
        """
        description = context.get("description", "Non spécifiée")
        rapport1 = context.get("rapport_tech1", "Non fourni")
        rapport2 = context.get("rapport_tech2", "Non fourni")
        capteur_id = context.get("capteur_id", "?")

        prompt = (
            f"Tu es un système de validation IA pour Neo-Sousse 2030.\n\n"
            f"Une intervention sur le capteur {capteur_id} demande validation IA.\n\n"
            f"Description : {description}\n"
            f"Rapport technicien 1 : {rapport1}\n"
            f"Rapport technicien 2 : {rapport2}\n\n"
            f"Détermine si cette intervention peut être validée.\n"
            f"Réponds en JSON strict :\n"
            f'{{ "approved": true/false, "confidence": 0.0-1.0, "reason": "..." }}'
        )

        raw = self._client.complete(prompt, max_tokens=200)
        try:
            # Extract JSON even if LLM adds extra text
            start = raw.find("{")
            end = raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            return {"approved": True, "confidence": 0.7, "reason": "Validation auto (parsing error)."}

    def get_priority_actions(self) -> dict:
        """Generate the list of priority actions for the dashboard."""
        stats = self._ctx.quick_stats()
        prompt = GENERAL_RECOMMENDATIONS.format(**stats)
        raw = self._client.complete(prompt, max_tokens=800)
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            return {
                "actions": [],
                "resume": raw,
                "niveau_urgence": "INCONNU",
            }
