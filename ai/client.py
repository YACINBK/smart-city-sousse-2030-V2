"""
LLM client abstraction.

Two implementations:
  - OpenAIClient: uses the OpenAI API (production)
  - MockLLMClient: returns deterministic strings (testing / offline)

Switch via USE_MOCK_LLM=true in .env or config/settings.py.
"""

from __future__ import annotations
from typing import Protocol

from config.settings import get_settings


class LLMClient(Protocol):
    def complete(self, prompt: str, max_tokens: int = 1500) -> str: ...


class OpenAIClient:
    def __init__(self):
        import openai
        settings = get_settings()
        self._client = openai.OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def complete(self, prompt: str, max_tokens: int = 1500) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""


class MockLLMClient:
    """Returns canned responses for testing without API calls."""

    _CANNED: dict[str, str] = {
        "rapport": (
            "## Rapport Mock\n\n"
            "**Résumé Exécutif** : Les données simulées indiquent une qualité d'air acceptable.\n\n"
            "**Zones Critiques** : Zone Nord (PM2.5 = 42 µg/m³).\n\n"
            "**Recommandations** :\n1. Réduire le trafic.\n2. Contrôler les émissions industrielles.\n3. Planter des arbres.\n\n"
            "**Niveau d'Alerte** : ORANGE"
        ),
        "actions": (
            '{"actions": [{'
            '"priorite": 1, "titre": "Intervention capteur C-001", '
            '"description": "Capteur hors service depuis 26h", '
            '"responsable": "technicien", "delai_heures": 2, '
            '"impact": "Restauration monitoring zone Nord"'
            '}], "resume": "Situation sous contrôle.", "niveau_urgence": "ORANGE"}'
        ),
        "clarification": "Souhaitez-vous (1) toutes les mesures ou (2) uniquement les PM2.5 ?",
        "validation": '{"approved": true, "confidence": 0.92, "reason": "Intervention conforme aux protocoles."}',
        "nl_back": "J'ai compris : vous voulez afficher les données demandées.",
    }

    def complete(self, prompt: str, max_tokens: int = 1500) -> str:
        prompt_lower = prompt.lower()
        if "rapport" in prompt_lower or "résumé" in prompt_lower or "qualité" in prompt_lower:
            return self._CANNED["rapport"]
        if "actions" in prompt_lower or "prioritaires" in prompt_lower:
            return self._CANNED["actions"]
        if "clarification" in prompt_lower or "ambiguïté" in prompt_lower:
            return self._CANNED["clarification"]
        if "approved" in prompt_lower or "valide" in prompt_lower or "intervention" in prompt_lower:
            return self._CANNED["validation"]
        if "sql" in prompt_lower or "traduis" in prompt_lower:
            return self._CANNED["nl_back"]
        return "Réponse simulée : données traitées avec succès."


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.use_mock_llm or not settings.openai_api_key:
        return MockLLMClient()
    return OpenAIClient()
