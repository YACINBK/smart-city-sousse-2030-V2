"""Report generation prompt templates."""

AIR_QUALITY_REPORT = """\
Tu es un expert en qualite de l'air urbain pour la ville intelligente Neo-Sousse 2030, Tunisie.

Voici les donnees agregees des capteurs de qualite d'air pour la periode {period} :

{data_summary}

Genere un rapport structure, lisible et decisionnel en francais avec les sections suivantes :

## Rapport Qualite de l'Air - {period}

1. **Resume Executif** (2-3 phrases)
2. **Tableau de Lecture Rapide** - 3 a 5 indicateurs cles sous forme de tableau Markdown
3. **Zones Critiques** - liste les zones depassant les seuils OMS (PM2.5 > 15 ug/m3, PM10 > 45 ug/m3)
4. **Tendances Observees** - hausse, baisse ou stabilite par rapport a la periode precedente
5. **Recommandations** - 3 actions concretes pour les gestionnaires urbains
6. **Niveau d'Alerte Global** - VERT / ORANGE / ROUGE (avec justification)

Regles :
- Reponse uniquement en Markdown
- Style clair, professionnel, non repetitif
- Phrases courtes
- Les recommandations doivent etre operationnelles
"""

INTERVENTION_REPORT = """\
Tu es un coordinateur technique pour la ville intelligente Neo-Sousse 2030.

Donnees des interventions pour la periode {period} :

{data_summary}

Genere un rapport de synthese en francais avec :

## Rapport Interventions - {period}

1. **Vue d'Ensemble** - nombre total, taux de resolution, delai moyen
2. **Interventions Critiques** - liste des interventions urgentes non resolues
3. **Performance des Equipes** - analyse des techniciens les plus actifs
4. **Points de Blocage** - interventions bloquees et raisons probables
5. **Recommandations** - 3 actions pour ameliorer l'efficacite

Regles :
- Reponse uniquement en Markdown
- Le rapport doit etre formule comme une note d'aide a la decision
- Utilise des sous-titres nets et quelques listes courtes
- Evite les phrases generiques
"""

SENSOR_STATUS_REPORT = """\
Tu es un ingenieur de maintenance pour le reseau de capteurs de Neo-Sousse 2030.

Etat actuel du reseau de capteurs :

{data_summary}

Genere un rapport de maintenance en francais :

## Rapport Etat des Capteurs - {period}

1. **Tableau de Bord** - actifs / signales / en maintenance / hors service
2. **Capteurs Prioritaires** - liste des capteurs necessitant une intervention immediate
3. **Analyse de Fiabilite** - taux de disponibilite par zone et par type
4. **Plan de Maintenance Suggere** - calendrier previsionnel base sur l'etat actuel
5. **Alertes** - capteurs hors service depuis plus de 24h

Regles :
- Reponse uniquement en Markdown
- Commence par une synthese courte
- Mets en evidence les capteurs ou categories prioritaires
- Termine par un mini plan d'action
"""

GENERAL_RECOMMENDATIONS = """\
Tu es un conseiller IA municipal pour Neo-Sousse 2030.

Situation actuelle de la ville :
- Capteurs hors service : {hors_service_count}
- Interventions en attente : {pending_interventions}
- Alertes actives (CRITICAL) : {critical_alerts}
- Zones depassant les seuils qualite air : {critical_zones}
- Vehicules en panne : {vehicles_breakdown}

Propose exactement 5 actions prioritaires pour les prochaines 24 heures.
Le ton doit etre professionnel, concret et oriente decision.
Les actions doivent etre ordonnees par priorite croissante (1 = la plus urgente).

Chaque action doit inclure :
- `priorite` : entier entre 1 et 5
- `titre` : intitule court et explicite
- `description` : ce qu'il faut faire, en une ou deux phrases
- `justification` : pourquoi cette action est prioritaire au vu des chiffres
- `responsable` : `technicien`, `gestionnaire` ou `IA`
- `delai_heures` : entier
- `impact` : effet operationnel attendu
- `indicateur_succes` : signe simple permettant de verifier que l'action a reussi

Reponds en JSON strict avec la structure :
{{
  "actions": [
    {{
      "priorite": 1,
      "titre": "...",
      "description": "...",
      "justification": "...",
      "responsable": "...",
      "delai_heures": 4,
      "impact": "...",
      "indicateur_succes": "..."
    }}
  ],
  "resume": "...",
  "niveau_urgence": "VERT|ORANGE|ROUGE"
}}

Contraintes :
- Pas de Markdown
- Pas de texte hors JSON
- Chaque recommandation doit etre differente
- Evite les formulations vagues
"""
