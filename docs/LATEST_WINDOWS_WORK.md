# Latest Windows Work Log

This document summarizes the latest work added from the Windows-based repair and verification pass.

## Scope

- align the live Docker app with the project requirements
- fix Linux/Windows runtime and documentation gaps
- make the IA module work with a real OpenAI-compatible provider through OpenRouter
- harden dashboard behavior so UI failures degrade safely instead of crashing

## Runtime And Deployment Changes

- `docker-compose.yml`
  - the app service now reads `.env`
  - the app seeds the database automatically on startup
  - the containerized app uses `db:5432`, while the host still connects on `localhost:5433`
- `.env.example`
  - documents `OPENAI_API_KEY`
  - documents `OPENAI_MODEL`
  - documents `OPENAI_BASE_URL`
- `config/settings.py`
  - adds support for `OPENAI_BASE_URL`

## Real LLM Setup

- `ai/client.py`
  - supports OpenAI-compatible providers by passing `base_url`
  - keeps offline fallback behavior if the remote call fails
- verified setup with OpenRouter
  - `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
  - `USE_MOCK_LLM=false`
- the live Docker app was verified to instantiate `OpenAIClient`

## Database And Seed Fixes

- `database/seed/seed_all.py`
  - keeps the seed orchestration explicit and idempotent unless `--force` is used
- `database/seed/seed_interventions.py`
  - fixes JSONB insertion by replacing the broken `:ai::jsonb` style with `CAST(:ai AS JSONB)`
- the seeded live dataset was verified after the repair pass
  - `zones=8`
  - `capteurs=50`
  - `mesures=76991`
  - `interventions=60`
  - `citoyens=100`
  - `vehicules=30`
  - `trajets=50`

## Compiler Fixes

- `compiler/semantic_analyzer.py`
  - normalizes enum values such as `hors_service`, `actif`, and `urgente`
  - rewrites `interventions en cours` to a valid semantic condition
  - supports cross-table average semantics
- `compiler/codegen.py`
  - generates the missing join for cross-table average queries
  - filters null PM2.5 rows for polluted-zone aggregation
- `compiler/parser.py`
  - makes superlative forms such as `le plus economique` emit `LIMIT 1`

## Dashboard Fixes

- `dashboard/pages/01_requetes.py`
  - ambiguity resolution now executes the selected interpretation
  - query visualization now degrades to the table if chart rendering fails
- `dashboard/components/chart_builder.py`
  - replaces fragile substring heuristics for time and geo columns
  - prevents timestamp columns such as `created_at` or `date_installation` from being treated as latitude
  - coerces map coordinates safely before sending them to Plotly
- `dashboard/components/fsm_widget.py`
  - renders SVG automata diagrams through HTML instead of `st.image(...)`
- `dashboard/pages/02_automates.py`
  - syncs FSM transitions back into `capteurs`, `interventions`, and `vehicules`
  - schedules and cancels delayed `HORS_SERVICE` alerts for sensors
- `dashboard/pages/03_rapports_ia.py`
  - improves the report layout
  - displays structured priority actions with description, justification, impact, delay, and success indicator
  - avoids dumping raw JSON into the page on parsing failure

## IA Report And Priority Actions Fixes

- `ai/prompts/report_templates.py`
  - reformulates report prompts to be more decision-oriented
  - reformulates `GENERAL_RECOMMENDATIONS` so the model returns richer operational actions
- `ai/action_advisor.py`
  - retries priority-action generation with a larger token budget when the first response is truncated
  - parses fenced JSON safely
  - sorts actions by priority after parsing
  - returns a controlled fallback message instead of showing the whole raw JSON payload
- `ai/client.py`
  - updates mock outputs so they match the newer structured contract

## FSM Clarification

The automata are workflow models, not graphs generated from raw telemetry every time.

- the graph itself is fixed by the FSM definition
- the selected entity is mapped to one current persisted state
- the highlighted node is that entity's current lifecycle state
- the history table and timeline show past transitions for that same entity

Examples:

- `SensorLifecycleFSM`
  - `INACTIF -> ACTIF -> SIGNALE -> EN_MAINTENANCE -> HORS_SERVICE`
- `InterventionWorkflowFSM`
  - `DEMANDE -> TECH1_ASSIGNE -> TECH2_VALIDE -> IA_VALIDE -> TERMINE`
- `VehicleRouteFSM`
  - `STATIONNE -> EN_ROUTE -> EN_PANNE -> ARRIVE`

## Windows-Specific Notes

- the repository copy used during this pass was not a git checkout, so branch publication required recreating git history from the GitHub remote
- the PowerShell environment on this machine blocks `.ps1` profile loading, which explains the repeated execution-policy warnings during shell commands
- Bash-first setup instructions were complemented with PowerShell usage notes
- the PDF filename uses non-ASCII characters; this is safe in the repo but can be awkward in some Windows CLI tools

## Verification

- local focused tests added for:
  - chart geo/time detection
  - action-advisor JSON parsing and retry behavior
  - updated mock IA outputs
- verified test runs during this repair pass:
  - local unit tests: `68 passed`
  - Docker unit tests: `68 passed`
  - Docker scenario tests: `55 passed`
  - focused parser/action tests after the latest priority-actions fix: `4 passed`

## Remaining Caveats

- the current repository still has text-encoding damage in some older files created before this pass
- the project still simulates a smart-city operational environment with seeded data; it is not a live IoT deployment
- a dedicated performance-benchmark section is still lighter than the rest of the deliverable and can be expanded later
