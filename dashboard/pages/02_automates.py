"""
Page 2 — Automates à États Finis

Features:
  - Entity selector (capteur | intervention | vehicule) + ID input
  - Current state badge
  - Transition trigger buttons (one per valid event)
  - Real-time Graphviz SVG (current state highlighted green)
  - FSM history timeline (Plotly Gantt)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from dashboard.components.fsm_widget import state_badge, transition_buttons, show_svg

st.set_page_config(page_title="Automates — Neo-Sousse 2030", page_icon="🔄", layout="wide")
st.title("🔄 Automates à États Finis")

# ── FSM instances ─────────────────────────────────────────────
@st.cache_resource
def get_fsm_instances():
    from fsm.sensor_fsm import SensorLifecycleFSM
    from fsm.intervention_fsm import InterventionWorkflowFSM
    from fsm.vehicle_fsm import VehicleRouteFSM
    from ai.action_advisor import ActionAdvisor
    advisor = ActionAdvisor()
    return {
        "capteur":      SensorLifecycleFSM(),
        "intervention": InterventionWorkflowFSM(ai_advisor_fn=advisor.validate_intervention),
        "vehicule":     VehicleRouteFSM(),
    }

@st.cache_resource
def get_repo():
    from fsm.persistence import FSMStateRepository
    return FSMStateRepository()

@st.cache_resource
def get_visualizer():
    from fsm.visualizer import GraphvizVisualizer
    return GraphvizVisualizer()

fsms = get_fsm_instances()
repo = get_repo()
viz = get_visualizer()

# ── Controls ──────────────────────────────────────────────────
col1, col2 = st.columns([2, 3])

with col1:
    entity_type = st.selectbox(
        "Type d'entité",
        options=["capteur", "intervention", "vehicule"],
        format_func=lambda x: {"capteur": "🔵 Capteur", "intervention": "🟡 Intervention",
                                "vehicule": "🚗 Véhicule"}[x],
    )
    entity_id = st.number_input("ID de l'entité", min_value=1, value=1, step=1)

    triggered_by = st.text_input("Déclenché par", value="user:dashboard")

    fsm = fsms[entity_type]

    # Load current state
    try:
        db_state = repo.get_state(entity_type, entity_id)
    except Exception:
        db_state = None

    current_state = db_state or fsm.initial_state

    st.markdown("**État actuel :**")
    state_badge(current_state)
    st.markdown("")

    # Transition buttons
    event = transition_buttons(fsm, current_state, on_trigger=None)

    if event:
        try:
            # Build context for guards
            ctx = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "tech1_id": 1,      # placeholder — dashboard could let user pick
                "tech2_id": 2,
                "rapport_tech1": "Anomalie confirmée par technicien 1.",
                "rapport_tech2": "Rapport technicien 2 : remplacement sonde requis.",
                "capteur_id": entity_id,
                "description": "Intervention déclenchée depuis le dashboard",
            }
            result = fsm.trigger(current_state, event, context=ctx)

            # Persist
            try:
                repo.set_state(entity_type, entity_id, result.to_state)
                repo.record_transition(
                    entity_type, entity_id,
                    result.from_state, event, result.to_state,
                    triggered_by=triggered_by,
                )

                # Sync capteurs.statut
                if entity_type == "capteur":
                    from database.connection import execute_query
                    execute_query(
                        "UPDATE capteurs SET statut=:s WHERE id=:id",
                        {"s": result.to_state, "id": entity_id},
                    )
            except Exception as db_err:
                st.warning(f"Transition effectuée mais non persistée : {db_err}")

            st.success(f"✅ Transition : **{result.from_state}** → **{result.to_state}**")

            if ctx.get("ai_validation"):
                ai_val = ctx["ai_validation"]
                st.info(
                    f"🤖 Validation IA : {'✅ Approuvée' if ai_val.get('approved') else '❌ Refusée'} "
                    f"(confiance : {ai_val.get('confidence', 0):.0%}) — {ai_val.get('reason', '')}"
                )

            current_state = result.to_state
            st.rerun()

        except Exception as e:
            st.error(f"❌ {e}")

with col2:
    # Graphviz SVG
    st.markdown("**Diagramme de l'automate :**")
    try:
        history = repo.get_history(entity_type, entity_id, limit=5)
        svg = viz.render(
            fsm,
            current_state=current_state,
            recent_transitions=history,
            title=f"{entity_type.capitalize()} #{entity_id} — État : {current_state}",
        )
        show_svg(svg)
    except Exception as e:
        st.warning(f"Visualisation indisponible : {e}")

# ── Transition table ──────────────────────────────────────────
with st.expander("📋 Table de transitions (delta)"):
    table = fsm.get_transition_table()
    df = pd.DataFrame(table)
    st.dataframe(df, use_container_width=True)

# ── History timeline ──────────────────────────────────────────
st.divider()
st.subheader("Historique des transitions")
try:
    history_full = repo.get_history(entity_type, entity_id, limit=50)
    if history_full:
        df_hist = pd.DataFrame(history_full)
        df_hist["triggered_at"] = pd.to_datetime(df_hist["triggered_at"])

        # Timeline Gantt
        if len(df_hist) >= 2:
            df_gantt = df_hist.copy()
            df_gantt["end"] = df_gantt["triggered_at"].shift(-1).fillna(datetime.utcnow())
            df_gantt["label"] = df_gantt["to_state"]
            fig = px.timeline(
                df_gantt,
                x_start="triggered_at", x_end="end",
                y="label", color="to_state",
                title=f"Durée passée dans chaque état — {entity_type} #{entity_id}",
                labels={"triggered_at": "Début", "end": "Fin", "label": "État"},
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("Aucun historique de transition enregistré.")
except Exception as e:
    st.warning(f"Historique indisponible : {e}")
