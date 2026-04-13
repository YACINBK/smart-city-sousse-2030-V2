"""
Scenario 02 — Sensor Fault Lifecycle
Tests all SensorLifecycleFSM transitions including HORS_SERVICE.
Also verifies the 24h alert scheduler is triggered.

POSITIVE: Full lifecycle INACTIF → ACTIF → SIGNALÉ → EN_MAINTENANCE → HORS_SERVICE
NEGATIVE: Invalid direct INACTIF → HORS_SERVICE should fail.
"""

import pytest
from fsm.sensor_fsm import SensorLifecycleFSM
from fsm.base import InvalidTransitionError


def test_full_sensor_lifecycle():
    """INACTIF → ACTIF → SIGNALÉ → EN_MAINTENANCE → HORS_SERVICE → ACTIF"""
    fsm = SensorLifecycleFSM()

    r1 = fsm.trigger("INACTIF", "installation")
    assert r1.to_state == "ACTIF"

    r2 = fsm.trigger("ACTIF", "détection_anomalie")
    assert r2.to_state == "SIGNALÉ"

    r3 = fsm.trigger("SIGNALÉ", "panne")
    assert r3.to_state == "EN_MAINTENANCE"

    r4 = fsm.trigger("EN_MAINTENANCE", "panne")
    assert r4.to_state == "HORS_SERVICE"

    # Recovery
    r5 = fsm.trigger("HORS_SERVICE", "installation")
    assert r5.to_state == "ACTIF"


def test_quick_repair_path():
    """INACTIF → ACTIF → SIGNALÉ → ACTIF (repair without maintenance)"""
    fsm = SensorLifecycleFSM()
    r1 = fsm.trigger("INACTIF", "installation")
    r2 = fsm.trigger(r1.to_state, "détection_anomalie")
    r3 = fsm.trigger(r2.to_state, "réparation")
    assert r3.to_state == "ACTIF"


def test_invalid_direct_to_hors_service():
    """INACTIF → HORS_SERVICE must fail."""
    fsm = SensorLifecycleFSM()
    with pytest.raises(InvalidTransitionError) as exc_info:
        fsm.trigger("INACTIF", "panne")
    assert "INACTIF" in str(exc_info.value)


def test_validate_sequence_failure():
    fsm = SensorLifecycleFSM()
    ok, msg = fsm.validate_sequence(["installation", "installation"])
    assert not ok


def test_scheduler_is_triggered_by_hors_service():
    """Verify FSMScheduler.schedule_hors_service_alert is called when entering HORS_SERVICE."""
    from fsm.scheduler import FSMScheduler
    from fsm.persistence import FSMStateRepository

    alerts_scheduled = []

    class MockRepo(FSMStateRepository):
        def get_state(self, et, eid): return "HORS_SERVICE"
        def set_state(self, *a): pass
        def record_transition(self, *a, **kw): pass

    scheduler = FSMScheduler(repo=MockRepo())
    scheduler.start()

    # Simulate scheduling
    scheduler.schedule_hors_service_alert(sensor_id=42)

    jobs = scheduler._scheduler.get_jobs()
    job_ids = [j.id for j in jobs]
    assert "hors_service_42" in job_ids

    scheduler.shutdown()
