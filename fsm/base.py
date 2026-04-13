"""
Custom FSM engine.

Design:
  - Transition table is a plain list of Transition objects — fully inspectable.
  - Guards are optional callables that must return True for the transition to fire.
  - Actions are optional callables that fire after a successful transition.
  - StateMachine instances are stateless; current state is passed in and returned.

This custom engine (vs. the `transitions` library) makes the delta function
explicit, enabling clean DB persistence, Graphviz rendering, and academic grading.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
from compiler.errors import CompilerError


class FSMError(Exception):
    pass


class InvalidTransitionError(FSMError):
    def __init__(self, state: str, event: str, valid_events: list[str]):
        self.state = state
        self.event = event
        self.valid_events = valid_events
        super().__init__(
            f"Transition invalide : l'événement '{event}' n'est pas permis depuis l'état '{state}'. "
            f"Événements valides : {valid_events or ['aucun']}."
        )


@dataclass
class Transition:
    source: str
    event: str
    target: str
    guard: Callable[[dict], bool] | None = None   # context dict → bool
    action: Callable[[dict], None] | None = None  # fires after transition


@dataclass
class TransitionResult:
    from_state: str
    event: str
    to_state: str
    action_result: Any = None


class StateMachine:
    """
    Base class for all automata.

    Subclasses define:
        states: list[str]
        initial_state: str
        transitions: list[Transition]

    State is NOT stored here — it is passed to trigger() and returned in TransitionResult.
    This makes the engine stateless and safe for use across DB-persisted entities.
    """

    states: list[str] = []
    initial_state: str = ""
    transitions: list[Transition] = []

    # ──────────────────────────────────────────────────────────

    def trigger(self, current_state: str, event: str,
                context: dict | None = None) -> TransitionResult:
        """
        Attempt to fire `event` from `current_state`.

        Args:
            current_state: The entity's current state string.
            event: The event name to trigger.
            context: Arbitrary dict passed to guard and action callables.

        Returns:
            TransitionResult with to_state if successful.

        Raises:
            InvalidTransitionError: If no valid transition exists.
        """
        ctx = context or {}
        matching = [
            t for t in self.transitions
            if t.source == current_state and t.event == event
        ]
        if not matching:
            valid = self.valid_events(current_state)
            raise InvalidTransitionError(current_state, event, valid)

        for t in matching:
            # Evaluate guard
            if t.guard is not None and not t.guard(ctx):
                continue
            # Fire action
            action_result = None
            if t.action is not None:
                action_result = t.action(ctx)
            return TransitionResult(
                from_state=current_state,
                event=event,
                to_state=t.target,
                action_result=action_result,
            )

        raise InvalidTransitionError(
            current_state, event,
            [t.event for t in self.transitions if t.source == current_state]
        )

    def valid_events(self, current_state: str) -> list[str]:
        """Return list of events that can fire from current_state (guards not evaluated)."""
        return list({t.event for t in self.transitions if t.source == current_state})

    def validate_sequence(self, events: list[str]) -> tuple[bool, str]:
        """
        Validate a sequence of events starting from initial_state.

        Returns:
            (True, final_state) if the sequence is valid.
            (False, error_message) if any transition is invalid.
        """
        state = self.initial_state
        for event in events:
            try:
                result = self.trigger(state, event)
                state = result.to_state
            except InvalidTransitionError as e:
                return False, str(e)
        return True, state

    def get_transition_table(self) -> list[dict]:
        """Return the transition table as a list of dicts (for Graphviz / display)."""
        return [
            {
                "source": t.source,
                "event": t.event,
                "target": t.target,
                "has_guard": t.guard is not None,
                "has_action": t.action is not None,
            }
            for t in self.transitions
        ]
