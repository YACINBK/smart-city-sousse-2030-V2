"""
VehicleRouteFSM

States:    STATIONNÉ → EN_ROUTE → EN_PANNE → ARRIVÉ
Events:    départ, panne, arrivée, réparation

Transition table (DFA):
┌────────────┬────────────┬────────────┐
│ Source     │ Event      │ Target     │
├────────────┼────────────┼────────────┤
│ STATIONNÉ  │ départ     │ EN_ROUTE   │
│ EN_ROUTE   │ panne      │ EN_PANNE   │
│ EN_ROUTE   │ arrivée    │ ARRIVÉ     │
│ EN_PANNE   │ réparation │ EN_ROUTE   │
│ ARRIVÉ     │ départ     │ EN_ROUTE   │  (next trip)
└────────────┴────────────┴────────────┘
"""

from fsm.base import StateMachine, Transition


class VehicleRouteFSM(StateMachine):

    states = ["STATIONNÉ", "EN_ROUTE", "EN_PANNE", "ARRIVÉ"]
    initial_state = "STATIONNÉ"

    transitions = [
        Transition(source="STATIONNÉ", event="départ",     target="EN_ROUTE"),
        Transition(source="EN_ROUTE",  event="panne",      target="EN_PANNE"),
        Transition(source="EN_ROUTE",  event="arrivée",    target="ARRIVÉ"),
        Transition(source="EN_PANNE",  event="réparation", target="EN_ROUTE"),
        Transition(source="ARRIVÉ",    event="départ",     target="EN_ROUTE"),   # next trip
    ]

    FINAL_STATES = {"ARRIVÉ"}
    CRITICAL_STATES = {"EN_PANNE"}
