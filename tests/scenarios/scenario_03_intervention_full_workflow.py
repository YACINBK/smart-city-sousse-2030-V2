"""
Scenario 03 — Full Intervention Workflow with AI Guard
DEMANDE → TECH1_ASSIGNÉ → TECH2_VALIDE → IA_VALIDE → TERMINÉ

POSITIVE: AI approves → reaches TERMINÉ.
NEGATIVE: AI rejects → blocked at IA_VALIDE.
"""

import pytest
from fsm.intervention_fsm import InterventionWorkflowFSM
from fsm.base import InvalidTransitionError


def _make_fsm(approved: bool) -> InterventionWorkflowFSM:
    return InterventionWorkflowFSM(
        ai_advisor_fn=lambda ctx: {
            "approved": approved,
            "confidence": 0.95 if approved else 0.2,
            "reason": "Approuvé" if approved else "Dossier incomplet",
        }
    )


def test_full_workflow_approved():
    fsm = _make_fsm(True)
    state = "DEMANDE"

    r = fsm.trigger(state, "assignation_tech1", {"tech1_id": 1})
    assert r.to_state == "TECH1_ASSIGNÉ"

    r = fsm.trigger(r.to_state, "validation_tech2",
                    {"tech2_id": 2, "rapport_tech1": "Anomalie confirmée"})
    assert r.to_state == "TECH2_VALIDE"

    ctx_ai = {"capteur_id": 5, "description": "Remplacement sonde",
              "rapport_tech1": "Sonde défaillante", "rapport_tech2": "Remplacement validé"}
    r = fsm.trigger(r.to_state, "validation_ia", ctx_ai)
    assert r.to_state == "IA_VALIDE"

    # ai_validation stored in context
    assert ctx_ai.get("ai_validation", {}).get("approved") is True

    r = fsm.trigger(r.to_state, "clôture", {})
    assert r.to_state == "TERMINÉ"


def test_ai_rejection_blocks_progress():
    fsm = _make_fsm(False)
    ctx_ai = {"capteur_id": 5, "description": "Rapport manquant",
              "rapport_tech1": "Incomplet", "rapport_tech2": "Incomplet"}

    with pytest.raises(InvalidTransitionError):
        fsm.trigger("TECH2_VALIDE", "validation_ia", ctx_ai)

    # Context should contain the AI decision
    assert ctx_ai.get("ai_validation", {}).get("approved") is False


def test_ai_validation_stored_in_context():
    fsm = _make_fsm(True)
    ctx = {"capteur_id": 1, "description": "Test",
           "rapport_tech1": "R1", "rapport_tech2": "R2"}
    fsm.trigger("TECH2_VALIDE", "validation_ia", ctx)
    assert "ai_validation" in ctx
    ai = ctx["ai_validation"]
    assert "approved" in ai and "confidence" in ai and "reason" in ai


def test_skip_steps_fails():
    fsm = _make_fsm(True)
    with pytest.raises(InvalidTransitionError):
        fsm.trigger("DEMANDE", "validation_ia", {})
