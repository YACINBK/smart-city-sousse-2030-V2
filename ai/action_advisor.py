"""
ActionAdvisor: validates FSM intervention transitions and suggests manager actions.
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

        Returns:
            {"approved": bool, "confidence": float, "reason": str}
        """
        description = context.get("description", "Non specifiee")
        rapport1 = context.get("rapport_tech1", "Non fourni")
        rapport2 = context.get("rapport_tech2", "Non fourni")
        capteur_id = context.get("capteur_id", "?")

        prompt = (
            "Tu es un systeme de validation IA pour Neo-Sousse 2030.\n\n"
            f"Une intervention sur le capteur {capteur_id} demande validation IA.\n\n"
            f"Description : {description}\n"
            f"Rapport technicien 1 : {rapport1}\n"
            f"Rapport technicien 2 : {rapport2}\n\n"
            "Determine si cette intervention peut etre validee.\n"
            'Reponds en JSON strict : { "approved": true/false, "confidence": 0.0-1.0, "reason": "..." }'
        )

        raw = self._client.complete(prompt, max_tokens=240)
        try:
            return self._parse_json_object(raw)
        except (json.JSONDecodeError, ValueError):
            return {
                "approved": True,
                "confidence": 0.7,
                "reason": "Validation auto (parsing error).",
            }

    def get_priority_actions(self) -> dict:
        """Generate the list of priority actions for the dashboard."""
        stats = self._ctx.quick_stats()
        prompt = GENERAL_RECOMMENDATIONS.format(**stats)

        attempts = (
            (prompt, 1600),
            (
                prompt
                + "\n\nIMPORTANT: renvoie une reponse COMPLETE, sans troncature, sans bloc Markdown, en un seul objet JSON valide.",
                2400,
            ),
        )

        last_raw = ""
        for current_prompt, max_tokens in attempts:
            raw = self._client.complete(current_prompt, max_tokens=max_tokens)
            last_raw = raw
            try:
                data = self._parse_json_object(raw)
                actions = data.get("actions", [])
                if isinstance(actions, list):
                    data["actions"] = sorted(actions, key=self._priority_rank)
                return data
            except (json.JSONDecodeError, ValueError):
                continue

        return {
            "actions": [],
            "resume": "La reponse IA n'a pas pu etre structuree correctement.",
            "niveau_urgence": "INCONNU",
            "raw_output": last_raw,
        }

    @staticmethod
    def _priority_rank(action: dict) -> int:
        try:
            return int(action.get("priorite", 999))
        except (TypeError, ValueError):
            return 999

    @staticmethod
    def _parse_json_object(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start = text.find("{")
        if start < 0:
            raise ValueError("No JSON object found.")

        depth = 0
        in_string = False
        escape = False
        end = None
        for index, char in enumerate(text[start:], start=start):
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break

        if end is None:
            raise ValueError("Truncated JSON response.")

        return json.loads(text[start:end])
