"""
Scenario 08 — Vehicle Route FSM
STATIONNÉ → EN_ROUTE → EN_PANNE → EN_ROUTE → ARRIVÉ
Also tests recovery path and multi-trip sequence.
"""

import pytest
from fsm.vehicle_fsm import VehicleRouteFSM
from fsm.base import InvalidTransitionError


@pytest.fixture
def fsm():
    return VehicleRouteFSM()


def test_normal_trip(fsm):
    ok, final = fsm.validate_sequence(["départ", "arrivée"])
    assert ok and final == "ARRIVÉ"


def test_trip_with_breakdown_and_recovery(fsm):
    ok, final = fsm.validate_sequence(["départ", "panne", "réparation", "arrivée"])
    assert ok and final == "ARRIVÉ"


def test_second_trip_from_arrive(fsm):
    ok, final = fsm.validate_sequence(["départ", "arrivée", "départ", "arrivée"])
    assert ok and final == "ARRIVÉ"


def test_breakdown_without_repair_cannot_arrive(fsm):
    ok, _ = fsm.validate_sequence(["départ", "panne", "arrivée"])
    assert not ok


def test_depart_from_en_panne_invalid(fsm):
    with pytest.raises(InvalidTransitionError):
        fsm.trigger("EN_PANNE", "départ")


def test_arrivee_from_stationnaire_invalid(fsm):
    with pytest.raises(InvalidTransitionError):
        fsm.trigger("STATIONNÉ", "arrivée")


def test_multiple_breakdowns(fsm):
    ok, final = fsm.validate_sequence([
        "départ", "panne", "réparation", "panne", "réparation", "arrivée"
    ])
    assert ok and final == "ARRIVÉ"


def test_transition_table_complete(fsm):
    table = fsm.get_transition_table()
    events = {t["event"] for t in table}
    assert {"départ", "panne", "arrivée", "réparation"}.issubset(events)
