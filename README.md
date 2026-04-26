# Smart City Sousse 2030 V2

Smart City Sousse 2030 V2 is a ready-to-run urban operations platform that combines a French natural-language-to-SQL compiler, finite-state workflow engines, AI-assisted reporting, and an interactive Streamlit control dashboard.

The application dashboard is branded as `Neo-Sousse 2030` and exposes the full platform through a single operator interface for data exploration, workflow supervision, and AI-supported decision-making.

## Overview

- Compile French business questions into parameterized SQL.
- Supervise sensor, intervention, and vehicle lifecycles with deterministic finite-state machines.
- Generate analytical reports and priority actions with either a real or mock LLM backend.
- Explore operational, relational, and time-series datasets from a unified dashboard.
- Run the platform locally or through Docker Compose.

## Core Capabilities

### 1. Natural Language Querying

The query module transforms French input into executable SQL through a compiler pipeline built around:

- lexical analysis
- parsing
- AST generation
- semantic validation
- SQL code generation

Operators can inspect the generated SQL, result table, chart output, and debugging pipeline in the same screen.

### 2. Workflow Automation With FSMs

The platform models three operational workflows as finite-state machines:

- `SensorLifecycleFSM`
- `InterventionWorkflowFSM`
- `VehicleRouteFSM`

Each workflow supports state visualization, guarded transitions, persistence, and transition history.

### 3. AI Reporting And Decision Support

The AI layer can:

- generate structured reports for air quality, interventions, and sensor status
- suggest priority actions with urgency levels
- validate intervention steps through an AI-assisted decision point
- run in offline mock mode when no API key is configured

### 4. Operational Dashboard

The Streamlit application includes four operator pages:

- `Queries`: natural language to SQL compilation and execution
- `Automata`: workflow visualization and transition control
- `AI Reports`: report generation, action prioritization, PDF export
- `Data Explorer`: sensors, measurements, interventions, and citizens

## Architecture

| Module | Responsibility |
| --- | --- |
| `compiler/` | Lexer, parser, AST, semantic analyzer, SQL generation |
| `fsm/` | State machines, scheduler, persistence, visualizer |
| `ai/` | LLM client, reports, recommendations, ambiguity handling |
| `database/` | Connection layer, schema, seed scripts |
| `dashboard/` | Streamlit app, pages, components, UI theme |
| `config/` | Runtime settings |
| `tests/` | Unit and scenario validation |

## Technology Stack

- Python 3.10+ (`3.11` recommended)
- Streamlit
- PostgreSQL
- TimescaleDB-compatible schema
- SQLAlchemy
- Plotly
- OpenAI-compatible API integration
- pytest

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- `pip`
- Docker Desktop for containerized execution
- Optional: Graphviz for richer FSM rendering

## Quick Start

### Option 1: Run The Full Stack With Docker Compose

This is the fastest way to start the complete platform with the database and dashboard together.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Access the dashboard at `http://localhost:8501`.

Notes:

- the application seeds the database automatically on startup
- PostgreSQL is exposed on `localhost:5433`
- inside Docker networking, the app connects to `db:5432`

### Option 2: Run The Dashboard Locally

Use this mode when you want the app process on your machine while keeping the database available through Docker or your own PostgreSQL instance.

If you use the database from `docker compose`, set:

- `DATABASE_URL=postgresql://neo_user:neo_password@localhost:5433/neo_sousse`

PowerShell setup:

```powershell
Copy-Item .env.example .env
docker compose up -d db
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql://neo_user:neo_password@localhost:5433/neo_sousse"
python database\seed\seed_all.py
streamlit run dashboard\app.py
```

Access the dashboard at `http://localhost:8501`.

## Database Initialization

The schema is stored in `database\schema.sql`.

- When you use Docker Compose, the database schema is initialized automatically.
- When you use your own PostgreSQL instance, apply the schema before seeding the data.

Manual initialization example:

```powershell
psql -h localhost -U neo_user -d neo_sousse -f database\schema.sql
python database\seed\seed_all.py
```

To rerun all seeders explicitly:

```powershell
python database\seed\seed_all.py --force
```

## Configuration

Copy `.env.example` to `.env` and adjust the values for your environment.

| Variable | Purpose | Example / Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://neo_user:neo_password@localhost:5432/neo_sousse` |
| `OPENAI_API_KEY` | API key for live LLM calls | `sk-...` |
| `USE_MOCK_LLM` | Enables offline deterministic AI responses | `false` |
| `OPENAI_MODEL` | Model identifier for the LLM client | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Optional endpoint for OpenAI-compatible providers | empty |
| `HORS_SERVICE_ALERT_DELAY_SECONDS` | Delay before scheduled sensor alert creation | `86400` |
| `TIMESCALE_ENABLED` | Feature flag for Timescale-oriented behavior | `true` |
| `FSM_HISTORY_ENABLED` | Enables FSM persistence history | `true` |

## AI Runtime Modes

### Mock Mode

Use mock mode for demos, testing, or offline execution.

```powershell
$env:USE_MOCK_LLM = "true"
streamlit run dashboard\app.py
```

### Live LLM Mode

Use live mode when you want real model-generated reports and actions.

Required configuration:

- `USE_MOCK_LLM=false`
- `OPENAI_API_KEY=<your_key>`

Optional configuration:

- `OPENAI_MODEL=<your_model>`
- `OPENAI_BASE_URL=<compatible_endpoint>`

## How To Use The Platform

1. Start the application and open `http://localhost:8501`.
2. Navigate through the sidebar pages.
3. In `Queries`, enter a French request and inspect the generated SQL and results.
4. In `Automata`, choose an entity type and trigger lifecycle transitions.
5. In `AI Reports`, generate reports and download PDF exports.
6. In `Data Explorer`, inspect the seeded operational dataset and time-series measurements.

## Example Natural Language Queries

| Input | Expected Intent |
| --- | --- |
| `Affiche les 5 zones les plus polluees` | list the most polluted areas |
| `Combien de capteurs sont hors service ?` | count unavailable sensors |
| `Quels citoyens ont un score ecologique > 80 ?` | retrieve top eco-score citizens |
| `Donne-moi le trajet le plus economique en CO2` | find the most CO2-efficient route |
| `Affiche les interventions avec priorite urgente` | filter urgent interventions |

## Testing

Run the automated test suites with mock AI enabled:

```powershell
$env:USE_MOCK_LLM = "true"
pytest tests\unit -q
pytest tests\scenarios -q
```

The test suite is designed to validate compiler behavior, FSM transitions, charting helpers, AI adapters, and end-to-end business scenarios.

## Entry Points

- Dashboard application: `dashboard\app.py`
- Full database seed: `database\seed\seed_all.py`
- Runtime configuration: `config\settings.py`

## Project Status

This repository represents the current packaged version of the platform, with a runnable dashboard, seeded data workflow, container support, automated tests, and configurable AI integration.
