"""FSM state badge + transition buttons + Graphviz SVG widget."""

import streamlit as st
from fsm.base import InvalidTransitionError

_STATE_COLORS = {
    "HORS_SERVICE":   "#dc3545",
    "EN_PANNE":       "#dc3545",
    "EN_MAINTENANCE": "#fd7e14",
    "SIGNALÉ":        "#ffc107",
    "ACTIF":          "#28a745",
    "EN_ROUTE":       "#28a745",
    "TECH1_ASSIGNÉ":  "#17a2b8",
    "TECH2_VALIDE":   "#17a2b8",
    "IA_VALIDE":      "#6f42c1",
    "TERMINÉ":        "#28a745",
    "ARRIVÉ":         "#28a745",
    "INACTIF":        "#6c757d",
    "DEMANDE":        "#6c757d",
    "STATIONNÉ":      "#6c757d",
}


def state_badge(state: str) -> None:
    color = _STATE_COLORS.get(state, "#6c757d")
    st.markdown(
        f'<div style="display:inline-block;background:{color};color:white;'
        f'padding:8px 20px;border-radius:20px;font-weight:bold;font-size:1.1em;">'
        f'{state}</div>',
        unsafe_allow_html=True,
    )


def transition_buttons(fsm, current_state: str, on_trigger) -> str | None:
    """Render one button per valid event. Returns the triggered event or None."""
    valid_events = fsm.valid_events(current_state)
    if not valid_events:
        st.info("Aucune transition disponible depuis cet état.")
        return None

    st.markdown("**Événements disponibles :**")
    cols = st.columns(min(len(valid_events), 4))
    for i, event in enumerate(valid_events):
        with cols[i % 4]:
            if st.button(f"▶ {event}", key=f"fsm_event_{event}_{current_state}"):
                return event
    return None


def show_svg(svg_bytes: bytes) -> None:
    if svg_bytes:
        st.image(svg_bytes, use_container_width=True)
