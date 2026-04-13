"""
SensorLifecycleFSM

States:    INACTIF → ACTIF → SIGNALÉ → EN_MAINTENANCE → HORS_SERVICE
Events:    installation, détection_anomalie, réparation, panne

Transition table (DFA):
┌──────────────────┬──────────────────────┬──────────────────┐
│ Source           │ Event                │ Target           │
├──────────────────┼──────────────────────┼──────────────────┤
│ INACTIF          │ installation         │ ACTIF            │
│ ACTIF            │ détection_anomalie   │ SIGNALÉ          │
│ SIGNALÉ          │ réparation           │ ACTIF            │
│ SIGNALÉ          │ panne                │ EN_MAINTENANCE   │
│ EN_MAINTENANCE   │ réparation           │ ACTIF            │
│ EN_MAINTENANCE   │ panne                │ HORS_SERVICE     │
│ HORS_SERVICE     │ installation         │ ACTIF            │
└──────────────────┴──────────────────────┴──────────────────┘
"""

from fsm.base import StateMachine, Transition


class SensorLifecycleFSM(StateMachine):

    states = ["INACTIF", "ACTIF", "SIGNALÉ", "EN_MAINTENANCE", "HORS_SERVICE"]
    initial_state = "INACTIF"

    # Actions are resolved via SideEffectRegistry at runtime
    transitions = [
        Transition(source="INACTIF",        event="installation",       target="ACTIF"),
        Transition(source="ACTIF",          event="détection_anomalie", target="SIGNALÉ"),
        Transition(source="SIGNALÉ",        event="réparation",         target="ACTIF"),
        Transition(source="SIGNALÉ",        event="panne",              target="EN_MAINTENANCE"),
        Transition(source="EN_MAINTENANCE", event="réparation",         target="ACTIF"),
        Transition(source="EN_MAINTENANCE", event="panne",              target="HORS_SERVICE"),
        Transition(source="HORS_SERVICE",   event="installation",       target="ACTIF"),
    ]

    FINAL_STATES = {"HORS_SERVICE"}
    CRITICAL_STATES = {"HORS_SERVICE", "EN_MAINTENANCE"}
