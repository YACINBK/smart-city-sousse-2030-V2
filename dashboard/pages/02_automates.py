"""Automates à états finis — visualisation, transitions, historique."""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components.chart_builder import _neon_fig
from dashboard.components.fsm_widget import show_svg, state_badge, transition_buttons
from dashboard.theme import apply_theme

st.set_page_config(page_title="Automates — Neo-Sousse 2030", layout="wide")
apply_theme()

st.markdown("# Automates à états finis")
st.caption(
    "Trois automates déterministes pilotent le cycle de vie des entités : "
    "capteurs, interventions et véhicules autonomes."
)


@st.cache_resource
def get_fsm_instances():
    from ai.action_advisor import ActionAdvisor
    from fsm.intervention_fsm import InterventionWorkflowFSM
    from fsm.sensor_fsm import SensorLifecycleFSM
    from fsm.vehicle_fsm import VehicleRouteFSM
    advisor = ActionAdvisor()
    return {
        "capteur": SensorLifecycleFSM(),
        "intervention": InterventionWorkflowFSM(ai_advisor_fn=advisor.validate_intervention),
        "vehicule": VehicleRouteFSM(),
    }


@st.cache_resource
def get_repo():
    from fsm.persistence import FSMStateRepository
    return FSMStateRepository()


@st.cache_resource
def get_visualizer():
    from fsm.visualizer import GraphvizVisualizer
    return GraphvizVisualizer()


@st.cache_resource
def get_scheduler():
    from fsm.scheduler import FSMScheduler

    scheduler = FSMScheduler(repo=get_repo())
    scheduler.start()
    return scheduler


def _sync_business_state(entity_type: str, entity_id: int, to_state: str, ctx: dict) -> None:
    from database.connection import execute_query

    if entity_type == "capteur":
        execute_query(
            "UPDATE capteurs SET statut=:s WHERE id=:id",
            {"s": to_state, "id": entity_id},
        )
        return

    if entity_type == "intervention":
        execute_query(
            """UPDATE interventions
               SET statut=:statut,
                   tech1_id=COALESCE(:tech1_id, tech1_id),
                   tech2_id=COALESCE(:tech2_id, tech2_id),
                   rapport_tech1=COALESCE(:rapport_tech1, rapport_tech1),
                   rapport_tech2=COALESCE(:rapport_tech2, rapport_tech2),
                   completed_at=CASE WHEN :statut='TERMINÉ' THEN NOW() ELSE completed_at END
               WHERE id=:id""",
            {
                "id": entity_id,
                "statut": to_state,
                "tech1_id": ctx.get("tech1_id"),
                "tech2_id": ctx.get("tech2_id"),
                "rapport_tech1": ctx.get("rapport_tech1"),
                "rapport_tech2": ctx.get("rapport_tech2"),
            },
        )
        if ctx.get("ai_validation") is not None:
            execute_query(
                "UPDATE interventions SET ai_validation=CAST(:ai AS JSONB) WHERE id=:id",
                {"id": entity_id, "ai": json.dumps(ctx["ai_validation"], ensure_ascii=False)},
            )
        return

    if entity_type == "vehicule":
        execute_query(
            "UPDATE vehicules SET statut=:s WHERE id=:id",
            {"s": to_state, "id": entity_id},
        )


fsms = get_fsm_instances()
repo = get_repo()
viz = get_visualizer()
scheduler = get_scheduler()


col_left, col_right = st.columns([2, 3], gap="large")

with col_left:
    entity_type = st.selectbox(
        "Type d'entité",
        options=["capteur", "intervention", "vehicule"],
        format_func=lambda x: {
            "capteur": "Capteur",
            "intervention": "Intervention",
            "vehicule": "Véhicule",
        }[x],
    )
    entity_id = st.number_input("Identifiant", min_value=1, value=1, step=1)
    triggered_by = st.text_input("Déclenché par", value="user:dashboard")

    fsm = fsms[entity_type]

    try:
        db_state = repo.get_state(entity_type, entity_id)
    except Exception:
        db_state = None
    current_state = db_state or fsm.initial_state

    st.markdown("**État actuel**")
    state_badge(current_state)
    st.markdown(" ")

    event = transition_buttons(fsm, current_state, on_trigger=None)

    if event:
        try:
            ctx = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "tech1_id": 1,
                "tech2_id": 2,
                "rapport_tech1": "Anomalie confirmée par technicien 1.",
                "rapport_tech2": "Rapport technicien 2 : remplacement sonde requis.",
                "capteur_id": entity_id,
                "description": "Intervention déclenchée depuis le tableau de bord",
            }
            result = fsm.trigger(current_state, event, context=ctx)

            try:
                repo.set_state(entity_type, entity_id, result.to_state)
                repo.record_transition(
                    entity_type, entity_id,
                    result.from_state, event, result.to_state,
                    triggered_by=triggered_by,
                )
                _sync_business_state(entity_type, entity_id, result.to_state, ctx)
                if entity_type == "capteur":
                    if result.to_state == "HORS_SERVICE":
                        scheduler.schedule_hors_service_alert(entity_id)
                    elif result.from_state == "HORS_SERVICE":
                        scheduler.cancel_hors_service_alert(entity_id)
            except Exception as db_err:
                st.warning(f"Transition appliquée mais non persistée — {db_err}")

            st.success(
                f"Transition acceptée : {result.from_state} → {result.to_state}"
            )

            if ctx.get("ai_validation"):
                ai_val = ctx["ai_validation"]
                statut = "approuvée" if ai_val.get("approved") else "refusée"
                st.info(
                    f"Validation IA — {statut} "
                    f"(confiance {ai_val.get('confidence', 0):.0%}). "
                    f"{ai_val.get('reason', '')}"
                )

            st.rerun()

        except Exception as exc:
            st.error(f"Transition refusée — {exc}")

with col_right:
    st.markdown("**Diagramme**")
    try:
        history = repo.get_history(entity_type, entity_id, limit=5)
        svg = viz.render(
            fsm,
            current_state=current_state,
            recent_transitions=history,
            title=f"{entity_type.capitalize()} #{entity_id} — état : {current_state}",
        )
        show_svg(*svg)
    except Exception as exc:
        st.caption(f"Visualisation indisponible — {exc}")


with st.expander("Table de transitions (delta)"):
    table = fsm.get_transition_table()
    st.dataframe(pd.DataFrame(table), use_container_width=True)


st.divider()
st.markdown("#### Historique des transitions")

try:
    history_full = repo.get_history(entity_type, entity_id, limit=50)
    if history_full:
        df_hist = pd.DataFrame(history_full)
        df_hist["triggered_at"] = pd.to_datetime(df_hist["triggered_at"])

        if len(df_hist) >= 2:
            df_gantt = df_hist.copy()
            df_gantt["end"] = df_gantt["triggered_at"].shift(-1).fillna(datetime.utcnow())
            df_gantt["label"] = df_gantt["to_state"]
            fig = px.timeline(
                df_gantt,
                x_start="triggered_at",
                x_end="end",
                y="label",
                color="to_state",
                title=f"Durée passée dans chaque état — {entity_type} #{entity_id}",
                labels={"triggered_at": "Début", "end": "Fin", "label": "État"},
            )
            fig.update_yaxes(autorange="reversed")
            _neon_fig(fig)
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0A0A0A",
                plot_bgcolor="#0A0A0A",
                font=dict(family="Roboto, sans-serif", color="#F0F0F0"),
                title_font=dict(family="STIX Two Text, serif", color="#BBF351"),
                colorway=["#BBF351", "#00BCFF", "#D97706", "#DC2626", "#6B7280"],
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_hist, use_container_width=True)
    else:
        st.caption("Aucun historique de transition enregistré pour cette entité.")
except Exception as exc:
    st.caption(f"Historique indisponible — {exc}")
