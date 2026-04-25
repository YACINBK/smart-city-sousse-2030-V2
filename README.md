# Neo-Sousse 2030

Plateforme intégrée de **compilation NL→SQL**, **automates à états finis** et
**IA générative** pour la gestion intelligente d'une métropole fictive.

Projet réalisé dans le cadre du module *Théorie des Langages et Compilation*
(Section IA 2 — 2025/2026).

## Vue d'ensemble

Le système permet de :

1. Poser une question en français et obtenir le SQL correspondant.
2. Piloter les cycles de vie métier des capteurs, interventions et véhicules.
3. Générer des rapports analytiques et des actions prioritaires via un LLM.
4. Explorer les données relationnelles et temporelles depuis un dashboard Streamlit.

## Architecture

```text
neo-sousse-2030/
├── compiler/        Pipeline lexer -> parser -> AST -> génération SQL
├── fsm/             Moteur d'automates + persistance + visualisation
├── ai/              Rapports, recommandations, validation d'interventions
├── database/        Schéma PostgreSQL, connexion, seeders
├── dashboard/       Application Streamlit et composants visuels
├── tests/           Tests unitaires + scénarios
└── config/          Paramètres applicatifs
```

| Composant | Stack | Description |
|-----------|-------|-------------|
| Compilateur NL→SQL | Python pur | Lexer, parser, AST, analyse sémantique, SQL paramétré |
| Moteur d'automates | moteur maison | Transitions, guards, persistance, historique |
| Module IA | OpenAI / mock local | Rapports, recommandations, validation IA |
| Dashboard | Streamlit + Plotly | Interface de contrôle et d'exploration |
| Base de données | PostgreSQL / TimescaleDB | Schéma 3FN, mesures temporelles |

## Quick Start

Prérequis : Python 3.11+, `pip`, PostgreSQL 14+ ou Docker, Graphviz recommandé.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
export DATABASE_URL=postgresql://neo_user:neo_password@localhost:5433/neo_sousse
python database/seed/seed_all.py
streamlit run dashboard/app.py
```

Sous PowerShell :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql://neo_user:neo_password@localhost:5433/neo_sousse"
python database/seed/seed_all.py
streamlit run dashboard/app.py
```

Si vous préférez lancer toute la stack conteneurisée :

```bash
docker compose up --build
```

Le service `app` lance automatiquement le seed au démarrage. Côté hôte Windows/Linux,
PostgreSQL est exposé sur le port `5433`; à l'intérieur du réseau Docker, l'application
utilise `db:5432`.

## Sans Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql://neo_user:neo_password@localhost:5432/neo_sousse
psql "$DATABASE_URL" -f database/schema.sql
python database/seed/seed_all.py
streamlit run dashboard/app.py
```

Le schéma gère désormais l'absence de TimescaleDB : l'application continue avec
une table `mesures` classique si l'extension n'est pas disponible.

## Mode hors ligne

Le module IA peut fonctionner sans clé API :

```bash
export USE_MOCK_LLM=true
streamlit run dashboard/app.py
```

Avec une clé API réelle :

- OpenAI direct :
  `OPENAI_API_KEY=...`
  `OPENAI_MODEL=gpt-4o-mini` (ou autre modèle compatible)
- Fournisseur compatible OpenAI, comme OpenRouter :
  `OPENAI_API_KEY=...`
  `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
  `OPENAI_MODEL=<modele-compatible-chez-votre-fournisseur>`

En mode hors ligne :

- les appels LLM retournent des réponses mock réalistes en français ;
- si une clé API est configurée mais que l'appel OpenAI échoue, le client repasse sur le mock ;
- la base de données est optionnelle ;
- le dashboard affiche `—` ou des états vides au lieu de planter si la DB est indisponible.

## Utilisation

```bash
# Tableau de bord
streamlit run dashboard/app.py

# Seed forcé même si des lignes existent déjà
python database/seed/seed_all.py --force

# Vérification rapide du compilateur
python -c "from compiler.pipeline import NLToSQLPipeline; print(NLToSQLPipeline().compile_safe('Affiche les 5 zones les plus polluées')['sql'])"
```

## Exemples de requêtes

| Langage naturel | SQL généré |
|-----------------|------------|
| Affiche les 5 zones les plus polluées | `SELECT zones.nom, AVG(mesures.pm25) AS avg_pm25 ... ORDER BY AVG(mesures.pm25) DESC LIMIT 5` |
| Combien de capteurs sont hors service ? | `SELECT COUNT(*) FROM capteurs WHERE capteurs.statut = :p1` |
| Quels citoyens ont un score écologique > 80 ? | `SELECT * FROM citoyens WHERE citoyens.score_ecolo > :p1` |
| Donne-moi le trajet le plus économique en CO2 | `SELECT * FROM trajets ORDER BY trajets.economie_co2 DESC LIMIT 1` |

## Automates implémentés

| Automate | États |
|----------|-------|
| Cycle de vie d'un capteur | INACTIF → ACTIF → SIGNALÉ → EN_MAINTENANCE → HORS_SERVICE |
| Validation d'intervention | DEMANDE → TECH1_ASSIGNÉ → TECH2_VALIDE → IA_VALIDE → TERMINÉ |
| Trajet d'un véhicule autonome | STATIONNÉ → EN_ROUTE → EN_PANNE → ARRIVÉ |

Si Graphviz n'est pas installé, la page **Automates** bascule automatiquement
sur une vue HTML de secours au lieu de bloquer le rendu.

## Tests

```bash
USE_MOCK_LLM=true pytest tests/unit/ -v
USE_MOCK_LLM=true pytest tests/scenarios/ -v -k "not integration"
```

Les fixtures de test injectent un mode mock DB/LLM pour permettre une exécution
hors ligne des scénarios principaux.

## Module

Module : Théorie des Langages et Compilation  
Section : IA 2  
Année universitaire : 2025/2026
