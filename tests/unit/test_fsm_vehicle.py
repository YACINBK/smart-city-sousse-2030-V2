"""Unit tests for VehicleRouteFSM."""

import pytest
from fsm.vehicle_fsm import VehicleRouteFSM
from fsm.base import InvalidTransitionError


@pytest.fixture
def fsm():
    return VehicleRouteFSM()


class TestVehicleFSM:
    def test_initial_state(self, fsm):
        assert fsm.initial_state == "STATIONNÉ"

    def test_depart(self, fsm):
        result = fsm.trigger("STATIONNÉ", "départ")
        assert result.to_state == "EN_ROUTE"

    def test_panne_en_route(self, fsm):
        result = fsm.trigger("EN_ROUTE", "panne")
        assert result.to_state == "EN_PANNE"

    def test_arrivee(self, fsm):
        result = fsm.trigger("EN_ROUTE", "arrivée")
        assert result.to_state == "ARRIVÉ"

    def test_reparation_from_panne(self, fsm):
        result = fsm.trigger("EN_PANNE", "réparation")
        assert result.to_state == "EN_ROUTE"

    def test_full_trip_no_incident(self, fsm):
        ok, final = fsm.validate_sequence(["départ", "arrivée"])
        assert ok and final == "ARRIVÉ"

    def test_trip_with_breakdown(self, fsm):
        ok, final = fsm.validate_sequence(["départ", "panne", "réparation", "arrivée"])
        assert ok and final == "ARRIVÉ"

    def test_invalid_arrivee_from_stationnaire(self, fsm):
        with pytest.raises(InvalidTransitionError):
            fsm.trigger("STATIONNÉ", "arrivée")

    def test_transition_table_size(self, fsm):
        assert len(fsm.transitions) == 5
