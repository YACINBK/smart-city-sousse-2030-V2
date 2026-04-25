"""
LLM client abstraction.

Two implementations:
  - OpenAIClient: uses the OpenAI-compatible API (production)
  - MockLLMClient: returns deterministic strings (testing / offline)

Switch via USE_MOCK_LLM=true in .env or config/settings.py.
"""

from __future__ import annotations

from typing import Protocol

from config.settings import get_settings

_MOCK_RESPONSES: dict[str, str] = {
    "report_air": (
        "## Rapport Qualite de l'Air\n\n"
        "### Resume executif\n"
        "La qualite de l'air reste globalement maitrisee, mais la Zone Industrielle et les "
        "axes les plus circules concentrent les depassements les plus reguliers sur la periode.\n\n"
        "### Tableau de lecture rapide\n"
        "| Indicateur | Lecture |\n"
        "|---|---|\n"
        "| Tendance globale | Legere degradation |\n"
        "| Zone la plus exposee | Zone Industrielle |\n"
        "| Niveau d'alerte | ORANGE |\n\n"
        "### Zones critiques\n"
        "- Zone Industrielle : depassements frequents aux heures de pointe.\n"
        "- Corniche : pics ponctuels lies au trafic et aux conditions meteo.\n\n"
        "### Recommandations\n"
        "1. Recalibrer les capteurs les plus sollicites avant la prochaine periode de pointe.\n"
        "2. Renforcer la surveillance sur les zones a trafic dense entre 7h-9h et 17h-19h.\n"
        "3. Declencher une verification ciblee des capteurs presentant des derives repetees."
    ),
    "report_interventions": (
        "## Rapport Interventions\n\n"
        "### Vue d'ensemble\n"
        "Le volume d'interventions reste soutenu, avec une part importante de dossiers encore "
        "ouverts dans les etats intermediaires du workflow.\n\n"
        "### Points operationnels\n"
        "- Les demandes urgentes doivent etre traitees avant les interventions de confort.\n"
        "- Les dossiers bloques au niveau `TECH1_ASSIGNE` ou `TECH2_VALIDE` doivent etre revus en priorite.\n"
        "- Les validations IA doivent etre reservees aux dossiers documentes de facon complete.\n\n"
        "### Actions recommandees\n"
        "1. Reprioriser les interventions `URGENTE` et `HAUTE` non cloturees.\n"
        "2. Verifier les dossiers sans rapport technique complet.\n"
        "3. Suivre separement les interventions en attente de validation IA."
    ),
    "report_capteurs": (
        "## Rapport Etat des Capteurs\n\n"
        "### Situation actuelle\n"
        "Le parc de capteurs reste majoritairement disponible, avec un noyau reduit mais critique "
        "d'equipements signales, en maintenance ou hors service.\n\n"
        "### Lecture maintenance\n"
        "- Les capteurs `HORS_SERVICE` ont un impact immediat sur la couverture des zones concernees.\n"
        "- Les capteurs `SIGNALE` doivent etre consideres comme a risque de bascule en maintenance.\n"
        "- Les capteurs `EN_MAINTENANCE` doivent faire l'objet d'un suivi de delai.\n\n"
        "### Plan suggere\n"
        "1. Traiter d'abord les capteurs hors service sur les zones a forte exposition.\n"
        "2. Programmer une maintenance preventive pour les capteurs les plus anciens.\n"
        "3. Consolider l'historique des incidents pour detecter les modeles recurrents."
    ),
    "action": (
        '{"actions": ['
        '{"priorite": 1, "titre": "Maintenance capteur C-12", '
        '"description": "Inspecter puis recalibrer immediatement le capteur C-12 afin de retablir des mesures fiables.", '
        '"justification": "Le capteur derive sur un secteur sensible et fausse l\'analyse de la qualite de l\'air.", '
        '"responsable": "technicien", "delai_heures": 2, '
        '"impact": "Restauration de la couverture de surveillance sur la zone Nord.", '
        '"indicateur_succes": "Retour a un taux d\'erreur inferieur a 3% sur les prochaines mesures."}, '
        '{"priorite": 2, "titre": "Repriorisation des interventions urgentes", '
        '"description": "Passer en revue les interventions non terminees et faire remonter les dossiers critiques devant les demandes de confort.", '
        '"justification": "Le stock d\'interventions en attente augmente le risque de saturation operationnelle.", '
        '"responsable": "gestionnaire", "delai_heures": 4, '
        '"impact": "Reduction du delai moyen de prise en charge des cas les plus sensibles.", '
        '"indicateur_succes": "Toutes les interventions urgentes ont un responsable assigne avant la fin de journee."}'
        '], '
        '"resume": "Les priorites immediates portent sur la fiabilite des capteurs critiques et la fluidite du traitement operationnel.", '
        '"niveau_urgence": "ORANGE"}'
    ),
    "sql": (
        "J'ai compris : vous voulez obtenir le resultat decrit par cette requete SQL, "
        "avec un resume lisible sans exposer les details techniques."
    ),
    "validation": (
        '{"approved": true, "confidence": 0.93, '
        '"reason": "Les rapports techniques sont coherents et la cloture est justifiee."}'
    ),
    "clarification": "Souhaitez-vous toutes les mesures ou uniquement les PM2.5 ?",
    "default": "Rapport genere automatiquement par le module IA de Neo-Sousse 2030.",
}


class LLMClient(Protocol):
    def complete(self, prompt: str, max_tokens: int = 1500) -> str: ...


class OpenAIClient:
    def __init__(self):
        import openai

        settings = get_settings()
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self._client = openai.OpenAI(**kwargs)
        self._model = settings.openai_model

    def complete(self, prompt: str, max_tokens: int = 1500) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception:
            # Honor the documented offline fallback when the API is unreachable.
            return MockLLMClient().complete(prompt, max_tokens=max_tokens)


class MockLLMClient:
    """Returns canned responses for testing without API calls."""

    def complete(self, prompt: str, max_tokens: int = 1500) -> str:
        prompt_lower = prompt.lower()
        if "rapport qualite de l'air" in prompt_lower or "qualite de l'air" in prompt_lower:
            return _MOCK_RESPONSES["report_air"]
        if "rapport interventions" in prompt_lower or "donnees des interventions" in prompt_lower:
            return _MOCK_RESPONSES["report_interventions"]
        if "rapport etat des capteurs" in prompt_lower or "etat actuel du reseau de capteurs" in prompt_lower:
            return _MOCK_RESPONSES["report_capteurs"]
        matchers = (
            ("clarification", ("clarification", "ambiguite")),
            ("action", ("actions prioritaires", "actions", "action", "prioritaires", "recommandations", "niveau_urgence")),
            ("validation", ("approved", "validation ia", "intervention peut etre validee")),
            ("sql", ("sql", "requete", "traduis cette requete")),
            ("rapport", ("rapport", "resume", "qualite", "capteurs", "interventions")),
        )
        for key, keywords in matchers:
            if any(keyword in prompt_lower for keyword in keywords):
                return _MOCK_RESPONSES[key]
        return _MOCK_RESPONSES["default"]


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.use_mock_llm or not settings.openai_api_key:
        return MockLLMClient()
    return OpenAIClient()
