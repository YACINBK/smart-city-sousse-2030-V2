"""
GraphvizVisualizer — generates SVG diagrams of FSM automata.

Bonus feature (+5%): graphical automaton visualization.

Features:
  - Current state highlighted in green
  - HORS_SERVICE / EN_PANNE / critical states in salmon/red
  - Last N triggered transitions highlighted in blue
  - Returns SVG bytes for direct use in Streamlit st.image()
"""

from __future__ import annotations
import graphviz


# State color palette
_STATE_COLORS = {
    "HORS_SERVICE": "tomato",
    "EN_PANNE":     "tomato",
    "EN_MAINTENANCE": "orange",
    "SIGNALÉ":      "lightyellow",
    "TERMINÉ":      "lightblue",
    "ARRIVÉ":       "lightblue",
}
_CURRENT_COLOR  = "lightgreen"
_DEFAULT_COLOR  = "white"
_RECENT_EDGE_COLOR = "royalblue"


class GraphvizVisualizer:

    def render(
        self,
        fsm,
        current_state: str | None = None,
        recent_transitions: list[dict] | None = None,
        title: str = "",
    ) -> bytes:
        """
        Generate an SVG diagram for the given FSM instance.

        Args:
            fsm: A StateMachine subclass instance (has .states and .transitions).
            current_state: The entity's current state (highlighted green).
            recent_transitions: List of {from_state, event, to_state} dicts
                                 (last N transitions, colored blue).
            title: Optional graph title.

        Returns:
            SVG bytes.
        """
        dot = graphviz.Digraph(
            format="svg",
            graph_attr={
                "rankdir": "LR",
                "bgcolor": "white",
                "fontname": "Helvetica",
                "label": title,
                "labelloc": "t",
                "fontsize": "14",
            },
            node_attr={
                "shape": "roundedbox",
                "style": "filled",
                "fontname": "Helvetica",
                "fontsize": "12",
            },
            edge_attr={
                "fontname": "Helvetica",
                "fontsize": "10",
            },
        )

        # Build set of recently fired (source → target) pairs for edge coloring
        recent_edges: set[tuple[str, str]] = set()
        if recent_transitions:
            for t in recent_transitions[-5:]:
                recent_edges.add((t.get("from_state", ""), t.get("to_state", "")))

        # ── Nodes ────────────────────────────────────────────
        for state in fsm.states:
            if state == current_state:
                color = _CURRENT_COLOR
                penwidth = "2.5"
            elif state in _STATE_COLORS:
                color = _STATE_COLORS[state]
                penwidth = "1"
            else:
                color = _DEFAULT_COLOR
                penwidth = "1"

            # Double-circle for final states
            is_final = hasattr(fsm, "FINAL_STATES") and state in fsm.FINAL_STATES
            shape = "doublecircle" if is_final else "roundedbox"

            dot.node(state, label=state, fillcolor=color, shape=shape, penwidth=penwidth)

        # ── Initial state arrow ───────────────────────────────
        dot.node("__start__", label="", shape="point", width="0.2", fillcolor="black")
        dot.edge("__start__", fsm.initial_state, arrowhead="vee")

        # ── Edges ─────────────────────────────────────────────
        for t in fsm.transitions:
            is_recent = (t.source, t.target) in recent_edges
            label = t.event
            if t.guard:
                label += "\n[garde]"

            dot.edge(
                t.source,
                t.target,
                label=label,
                color=_RECENT_EDGE_COLOR if is_recent else "black",
                penwidth="2.0" if is_recent else "1.0",
                fontcolor=_RECENT_EDGE_COLOR if is_recent else "black",
            )

        # Render to SVG bytes
        svg_bytes = dot.pipe()
        return svg_bytes
