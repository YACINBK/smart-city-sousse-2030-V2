"""FSM helper widgets: state badge, transition controls, SVG renderer."""

import streamlit as st
import streamlit.components.v1 as components

_BAD_STATES = {"HORS_SERVICE", "EN_PANNE"}
_STATE_TONE = {
    "INACTIF":        "idle",
    "STATIONNÉ":      "idle",
    "DEMANDE":        "idle",
    "ACTIF":          "good",
    "EN_ROUTE":       "good",
    "TERMINÉ":        "good",
    "ARRIVÉ":         "good",
    "SIGNALÉ":        "warn",
    "EN_MAINTENANCE": "warn",
    "TECH1_ASSIGNÉ":  "info",
    "TECH2_VALIDE":   "info",
    "IA_VALIDE":      "info",
    "HORS_SERVICE":   "bad",
    "EN_PANNE":       "bad",
}


def state_badge(state: str) -> None:
    tone = _STATE_TONE.get(state, "idle")
    st.markdown(
        f'<span class="ns-tag {tone}">{state}</span>',
        unsafe_allow_html=True,
    )


def transition_buttons(fsm, current_state: str, on_trigger=None) -> str | None:
    """Render one button per valid event; returns the triggered event or None."""
    valid_events = fsm.valid_events(current_state)
    if not valid_events:
        st.caption("Aucune transition disponible depuis cet état.")
        return None

    st.markdown("**Événements**")
    risky_events = [
        event for event in valid_events
        if any(
            transition.source == current_state
            and transition.event == event
            and transition.target in _BAD_STATES
            for transition in fsm.transitions
        )
    ]
    standard_events = [event for event in valid_events if event not in risky_events]

    for events, is_risky in ((standard_events, False), (risky_events, True)):
        if not events:
            continue
        cols = st.columns(min(len(events), 4))
        for i, event in enumerate(events):
            with cols[i % 4]:
                if is_risky:
                    st.markdown(
                        '<span class="ns-tag bad" style="font-size:0.7rem">RISQUE</span>',
                        unsafe_allow_html=True,
                    )
                if st.button(
                    event,
                    key=f"fsm_event_{event}_{current_state}",
                    type="primary" if is_risky else "secondary",
                    use_container_width=True,
                ):
                    if on_trigger:
                        on_trigger(event)
                    return event
    return None


def show_svg(svg_bytes: bytes | None, fallback_html: str | None = None) -> None:
    if svg_bytes:
        try:
            svg_text = svg_bytes.decode("utf-8")
            components.html(
                f"""
                <div style="width:100%;overflow:auto;background:transparent;padding:0.25rem 0;">
                  {svg_text}
                </div>
                """,
                height=520,
                scrolling=True,
            )
        except Exception:
            st.image(svg_bytes, use_container_width=True)
    elif fallback_html:
        st.markdown(fallback_html, unsafe_allow_html=True)
