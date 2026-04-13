"""
Scenario 09 — Timed Alert Trigger (30s delay in test mode)
Sensor enters HORS_SERVICE → scheduler fires after 30s → alert created.

HORS_SERVICE_ALERT_DELAY_SECONDS=30 is set in conftest via env var.
"""

import os
import time
import pytest

# Use very short delay for testing
os.environ["HORS_SERVICE_ALERT_DELAY_SECONDS"] = "2"

from fsm.scheduler import FSMScheduler
from fsm.persistence import FSMStateRepository


class MockFSMRepo(FSMStateRepository):
    """In-memory repo that always returns HORS_SERVICE for sensor 99."""

    def get_state(self, entity_type, entity_id):
        if entity_type == "capteur" and entity_id == 99:
            return "HORS_SERVICE"
        return None

    def set_state(self, *a): pass
    def record_transition(self, *a, **kw): pass


def test_alert_fires_after_delay(monkeypatch):
    """Scheduler fires _check_and_alert after 2s delay; mock captures the call."""
    alerts_fired = []

    def mock_persist(sensor_id):
        alerts_fired.append(sensor_id)

    repo = MockFSMRepo()
    scheduler = FSMScheduler(repo=repo)
    scheduler.start()

    # Patch the persistence method
    monkeypatch.setattr(scheduler, "_persist_critical_alert", mock_persist)

    scheduler.schedule_hors_service_alert(sensor_id=99)

    # Wait for the job to fire (delay = 2s)
    time.sleep(3.5)

    assert 99 in alerts_fired, "Alert should have fired for sensor 99"

    scheduler.shutdown()


def test_cancel_prevents_alert(monkeypatch):
    """Cancelling before the delay fires → alert should NOT fire."""
    alerts_fired = []

    def mock_persist(sensor_id):
        alerts_fired.append(sensor_id)

    repo = MockFSMRepo()
    scheduler = FSMScheduler(repo=repo)
    scheduler.start()

    monkeypatch.setattr(scheduler, "_persist_critical_alert", mock_persist)

    scheduler.schedule_hors_service_alert(sensor_id=100)
    scheduler.cancel_hors_service_alert(sensor_id=100)

    time.sleep(3.5)

    assert 100 not in alerts_fired, "Alert should have been cancelled"

    scheduler.shutdown()


def test_replaced_job_fires_once():
    """Scheduling the same sensor twice → only fires once (replace_existing=True)."""
    repo = MockFSMRepo()
    scheduler = FSMScheduler(repo=repo)
    scheduler.start()

    scheduler.schedule_hors_service_alert(99)
    scheduler.schedule_hors_service_alert(99)  # replace

    jobs = [j for j in scheduler._scheduler.get_jobs() if "99" in j.id]
    assert len(jobs) == 1

    scheduler.shutdown()
