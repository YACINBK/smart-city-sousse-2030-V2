"""Unit tests for SensorLifecycleFSM."""

import pytest
from fsm.sensor_fsm import SensorLifecycleFSM
from fsm.base import InvalidTransitionError


@pytest.fixture
def fsm():
    return SensorLifecycleFSM()


class TestSensorFSM:
    def test_initial_state(self, fsm):
        assert fsm.initial_state == "INACTIF"

    def test_installation(self, fsm):
        result = fsm.trigger("INACTIF", "installation")
        assert result.to_state == "ACTIF"

    def test_anomalie_detection(self, fsm):
        result = fsm.trigger("ACTIF", "détection_anomalie")
        assert result.to_state == "SIGNALÉ"

    def test_repair_from_signale(self, fsm):
        result = fsm.trigger("SIGNALÉ", "réparation")
        assert result.to_state == "ACTIF"

    def test_panne_from_signale(self, fsm):
        result = fsm.trigger("SIGNALÉ", "panne")
        assert result.to_state == "EN_MAINTENANCE"

    def test_repair_from_maintenance(self, fsm):
        result = fsm.trigger("EN_MAINTENANCE", "réparation")
        assert result.to_state == "ACTIF"

    def test_panne_to_hors_service(self, fsm):
        result = fsm.trigger("EN_MAINTENANCE", "panne")
        assert result.to_state == "HORS_SERVICE"

    def test_reinstall_from_hors_service(self, fsm):
        result = fsm.trigger("HORS_SERVICE", "installation")
        assert result.to_state == "ACTIF"

    def test_invalid_transition_raises(self, fsm):
        with pytest.raises(InvalidTransitionError):
            fsm.trigger("INACTIF", "panne")

    def test_invalid_from_active(self, fsm):
        with pytest.raises(InvalidTransitionError):
            fsm.trigger("ACTIF", "installation")

    def test_valid_sequence(self, fsm):
        ok, final = fsm.validate_sequence([
            "installation", "détection_anomalie", "panne", "réparation"
        ])
        assert ok
        assert final == "ACTIF"

    def test_invalid_sequence(self, fsm):
        ok, msg = fsm.validate_sequence(["installation", "réparation"])
        assert not ok
        assert "réparation" in msg or "invalide" in msg.lower()

    def test_transition_table_completeness(self, fsm):
        table = fsm.get_transition_table()
        assert len(table) == 7  # exactly 7 transitions defined

    def test_valid_events_from_inactif(self, fsm):
        events = fsm.valid_events("INACTIF")
        assert "installation" in events

    def test_no_events_from_hors_service_except_install(self, fsm):
        events = fsm.valid_events("HORS_SERVICE")
        assert events == ["installation"]
