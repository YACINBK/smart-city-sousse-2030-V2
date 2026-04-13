"""Pytest fixtures for unit tests and scenario tests."""

import sys
import os
import pytest

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Always use MockLLMClient in tests (no API calls)
os.environ.setdefault("USE_MOCK_LLM", "true")
os.environ.setdefault("HORS_SERVICE_ALERT_DELAY_SECONDS", "30")


@pytest.fixture(scope="session")
def pipeline():
    from compiler.pipeline import NLToSQLPipeline
    return NLToSQLPipeline()


@pytest.fixture(scope="session")
def sensor_fsm():
    from fsm.sensor_fsm import SensorLifecycleFSM
    return SensorLifecycleFSM()


@pytest.fixture(scope="session")
def intervention_fsm():
    from fsm.intervention_fsm import InterventionWorkflowFSM
    # AI guard always approves in tests
    return InterventionWorkflowFSM(ai_advisor_fn=lambda ctx: {
        "approved": True, "confidence": 0.99, "reason": "Mock approval"
    })


@pytest.fixture(scope="session")
def vehicle_fsm():
    from fsm.vehicle_fsm import VehicleRouteFSM
    return VehicleRouteFSM()
