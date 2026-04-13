"""Report generation prompt templates."""

AIR_QUALITY_REPORT = """\
Tu es un expert en qualité de l'air urbain pour la ville intelligente Neo-Sousse 2030, Tunisie.

Voici les données agrégées des capteurs de qualité d'air pour la période {period} :

{data_summary}

Génère un rapport structuré en français avec les sections suivantes :

## Rapport Qualité de l'Air — {period}

1. **Résumé Exécutif** (2-3 phrases)
2. **Zones Critiques** — liste les zones dépassant les seuils OMS (PM2.5 > 15 µg/m³, PM10 > 45 µg/m³)
3. **Tendances Observées** — hausse, baisse ou stabilité par rapport à la période précédente
4. **Recommandations** — 3 actions concrètes pour les gestionnaires urbains
5. **Niveau d'Alerte Global** — VERT / ORANGE / ROUGE (avec justification)

Réponds uniquement avec le rapport formaté en Markdown. Sois précis et factuel.
"""

INTERVENTION_REPORT = """\
Tu es un coordinateur technique pour la ville intelligente Neo-Sousse 2030.

Données des interventions pour la période {period} :

{data_summary}

Génère un rapport de synthèse en français avec :

## Rapport Interventions — {period}

1. **Vue d'Ensemble** — nombre total, taux de résolution, délai moyen
2. **Interventions Critiques** — liste des interventions urgentes non résolues
3. **Performance des Équipes** — analyse des techniciens les plus actifs
4. **Points de Blocage** — interventions bloquées et raisons probables
5. **Recommandations** — 3 actions pour améliorer l'efficacité

Format Markdown, factuel et concis.
"""

SENSOR_STATUS_REPORT = """\
Tu es un ingénieur de maintenance pour le réseau de capteurs de Neo-Sousse 2030.

État actuel du réseau de capteurs :

{data_summary}

Génère un rapport de maintenance en français :

## Rapport État des Capteurs — {period}

1. **Tableau de Bord** — actifs / signalés / en maintenance / hors service
2. **Capteurs Prioritaires** — liste des capteurs nécessitant une intervention immédiate
3. **Analyse de Fiabilité** — taux de disponibilité par zone et par type
4. **Plan de Maintenance Suggéré** — calendrier prévisionnel basé sur l'état actuel
5. **Alertes** — capteurs hors service depuis plus de 24h

Format Markdown.
"""

GENERAL_RECOMMENDATIONS = """\
Tu es un conseiller IA municipal pour Neo-Sousse 2030.

Situation actuelle de la ville :
- Capteurs hors service : {hors_service_count}
- Interventions en attente : {pending_interventions}
- Alertes actives (CRITICAL) : {critical_alerts}
- Zones dépassant les seuils qualité air : {critical_zones}
- Véhicules en panne : {vehicles_breakdown}

Propose 5 actions prioritaires pour les prochaines 24 heures.
Chaque action doit inclure :
- Priorité (1 = urgente, 5 = basse)
- Responsable suggéré (technicien, gestionnaire, IA)
- Délai estimé de résolution
- Impact attendu sur la ville

Réponds en JSON strict avec la structure :
{{
  "actions": [
    {{
      "priorite": 1,
      "titre": "...",
      "description": "...",
      "responsable": "...",
      "delai_heures": 4,
      "impact": "..."
    }}
  ],
  "resume": "...",
  "niveau_urgence": "VERT|ORANGE|ROUGE"
}}
"""
