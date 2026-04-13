"""Unit tests for InterventionWorkflowFSM."""

import pytest
from fsm.intervention_fsm import InterventionWorkflowFSM
from fsm.base import InvalidTransitionError


@pytest.fixture
def fsm():
    return InterventionWorkflowFSM(
        ai_advisor_fn=lambda ctx: {"approved": True, "confidence": 0.95, "reason": "OK"}
    )


@pytest.fixture
def fsm_ai_rejects():
    return InterventionWorkflowFSM(
        ai_advisor_fn=lambda ctx: {"approved": False, "confidence": 0.3,
                                   "reason": "Dossier incomplet"}
    )


class TestInterventionFSM:
    def test_initial_state(self, fsm):
        assert fsm.initial_state == "DEMANDE"

    def test_assign_tech1(self, fsm):
        result = fsm.trigger("DEMANDE", "assignation_tech1", {"tech1_id": 1})
        assert result.to_state == "TECH1_ASSIGNÉ"

    def test_validate_tech2(self, fsm):
        ctx = {"tech2_id": 2, "rapport_tech1": "Anomalie confirmée"}
        result = fsm.trigger("TECH1_ASSIGNÉ", "validation_tech2", ctx)
        assert result.to_state == "TECH2_VALIDE"

    def test_ai_validates(self, fsm):
        ctx = {"capteur_id": 1, "description": "Test", "rapport_tech1": "R1", "rapport_tech2": "R2"}
        result = fsm.trigger("TECH2_VALIDE", "validation_ia", ctx)
        assert result.to_state == "IA_VALIDE"

    def test_ai_rejects_blocks_transition(self, fsm_ai_rejects):
        ctx = {"capteur_id": 1, "description": "Test", "rapport_tech1": "R1", "rapport_tech2": "R2"}
        with pytest.raises(InvalidTransitionError):
            fsm_ai_rejects.trigger("TECH2_VALIDE", "validation_ia", ctx)

    def test_full_workflow(self, fsm):
        ctx1 = {"tech1_id": 1}
        ctx2 = {"tech2_id": 2, "rapport_tech1": "Problème détecté"}
        ctx3 = {"capteur_id": 1, "description": "Intervention urgente",
                "rapport_tech1": "Rapport T1", "rapport_tech2": "Rapport T2"}

        r1 = fsm.trigger("DEMANDE", "assignation_tech1", ctx1)
        r2 = fsm.trigger(r1.to_state, "validation_tech2", ctx2)
        r3 = fsm.trigger(r2.to_state, "validation_ia", ctx3)
        r4 = fsm.trigger(r3.to_state, "clôture", {})

        assert r4.to_state == "TERMINÉ"

    def test_guard_no_tech1_blocks(self, fsm):
        with pytest.raises(InvalidTransitionError):
            fsm.trigger("DEMANDE", "assignation_tech1", {"tech1_id": None})

    def test_invalid_skip_step(self, fsm):
        with pytest.raises(InvalidTransitionError):
            fsm.trigger("DEMANDE", "validation_ia", {})
