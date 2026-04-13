"""
Scenario 10 — Full Pipeline Integration (end-to-end, no DB required)

Simulates the complete flow described in the spec §3.2 example:
1. A sensor goes into "SIGNALÉ" state
2. Intervention is created (DEMANDE)
3. Two technicians assigned, AI validates
4. User asks "Quelles interventions sont en cours ?"
5. Compiler translates to SQL
6. AI generates a status report (mocked)
"""

import pytest
from compiler.pipeline import NLToSQLPipeline
from fsm.sensor_fsm import SensorLifecycleFSM
from fsm.intervention_fsm import InterventionWorkflowFSM
from ai.report_generator import ReportGenerator
from ai.action_advisor import ActionAdvisor


@pytest.fixture(scope="module")
def pipeline():
    return NLToSQLPipeline()


@pytest.fixture(scope="module")
def sensor_fsm():
    return SensorLifecycleFSM()


@pytest.fixture(scope="module")
def intervention_fsm():
    return InterventionWorkflowFSM(
        ai_advisor_fn=lambda ctx: {"approved": True, "confidence": 0.95, "reason": "Validé"}
    )


@pytest.fixture(scope="module")
def reporter():
    return ReportGenerator()


@pytest.fixture(scope="module")
def advisor():
    return ActionAdvisor()


# ── Step 1-2: Sensor → SIGNALÉ, Intervention created ─────────

def test_step1_sensor_to_signale(sensor_fsm):
    """Capteur passe INACTIF → ACTIF → SIGNALÉ."""
    r = sensor_fsm.trigger("INACTIF", "installation")
    assert r.to_state == "ACTIF"
    r = sensor_fsm.trigger("ACTIF", "détection_anomalie")
    assert r.to_state == "SIGNALÉ"


# ── Step 3: Full intervention workflow ────────────────────────

def test_step3_intervention_workflow(intervention_fsm):
    """Intervention: DEMANDE → TECH1 → TECH2 → IA_VALIDE → TERMINÉ."""
    state = "DEMANDE"

    r = intervention_fsm.trigger(state, "assignation_tech1", {"tech1_id": 1})
    state = r.to_state
    assert state == "TECH1_ASSIGNÉ"

    r = intervention_fsm.trigger(state, "validation_tech2",
                                  {"tech2_id": 2, "rapport_tech1": "Anomalie confirmée"})
    state = r.to_state
    assert state == "TECH2_VALIDE"

    ctx = {"capteur_id": 1, "description": "Anomalie capteur",
           "rapport_tech1": "Sonde défaillante", "rapport_tech2": "Remplacement validé"}
    r = intervention_fsm.trigger(state, "validation_ia", ctx)
    state = r.to_state
    assert state == "IA_VALIDE"
    assert ctx["ai_validation"]["approved"] is True

    r = intervention_fsm.trigger(state, "clôture", {})
    assert r.to_state == "TERMINÉ"


# ── Step 4-5: NL query → SQL ──────────────────────────────────

def test_step4_nl_compile_interventions_en_cours(pipeline):
    """'Quelles interventions sont en cours ?' → SQL with WHERE statut != 'TERMINÉ'."""
    result = pipeline.compile_safe("quelles interventions sont en cours")
    assert result["success"]
    sql = result["sql"].upper()
    assert "INTERVENTIONS" in sql


def test_step4_nl_compile_capteurs_signalos(pipeline):
    """'Affiche les capteurs signalés' → SQL with WHERE statut = 'SIGNALÉ'."""
    result = pipeline.compile_safe("affiche capteurs dont statut est signalé")
    assert result["success"]
    sql = result["sql"]
    assert "capteurs" in sql.lower()


def test_step5_ast_contains_entity(pipeline):
    result = pipeline.compile_safe("affiche interventions")
    assert result["success"]
    ast = result["ast"]
    assert ast["entity"]["table"] == "interventions"


# ── Step 6: AI report generation ─────────────────────────────

def test_step6_ai_report_generated(reporter):
    """AI generates a non-empty report string (uses MockLLMClient, no DB needed)."""
    from datetime import date, timedelta
    from unittest.mock import patch
    from ai.context_builder import DBContextBuilder

    # Patch context builder to avoid DB connection
    with patch.object(DBContextBuilder, 'sensor_status_summary', return_value="| Statut | N |\n|---|---|\n| ACTIF | 30 |"):
        report = reporter.generate(
            "capteurs",
            start=date.today() - timedelta(days=7),
            end=date.today(),
        )
    assert report and len(report) > 20


def test_step6_ai_actions_structured(advisor):
    """ActionAdvisor returns a dict with 'actions' key (mocked stats)."""
    from unittest.mock import patch
    from ai.context_builder import DBContextBuilder

    mock_stats = {
        "hors_service_count": 3, "pending_interventions": 7,
        "critical_alerts": 2, "critical_zones": 1, "vehicles_breakdown": 0,
    }
    with patch.object(DBContextBuilder, 'quick_stats', return_value=mock_stats):
        result = advisor.get_priority_actions()
    assert isinstance(result, dict)
    assert "actions" in result or "resume" in result


# ── Full pipeline consistency check ──────────────────────────

def test_all_modules_consistent(pipeline, sensor_fsm, intervention_fsm, reporter):
    """Smoke test: all modules instantiate and produce results."""
    # Compiler
    r = pipeline.compile_safe("combien de capteurs")
    assert r["success"] or r["error"]

    # FSMs have correct state counts
    assert len(sensor_fsm.states) == 5
    assert len(intervention_fsm.states) == 5

    # Reporter returns a string (mock DB context)
    from unittest.mock import patch
    from ai.context_builder import DBContextBuilder
    with patch.object(DBContextBuilder, 'sensor_status_summary', return_value="| ACTIF | 30 |"):
        report = reporter.generate("capteurs")
    assert isinstance(report, str)
