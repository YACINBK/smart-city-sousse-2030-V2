"""Rapports analytiques generes par le module d'IA."""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from ai.action_advisor import ActionAdvisor
from ai.report_generator import REPORT_TYPES, ReportGenerator
from dashboard.theme import apply_theme

st.set_page_config(page_title="Rapports IA - Neo-Sousse 2030", layout="wide")
apply_theme()

st.markdown("# Rapports analytiques")
st.caption(
    "Le module d'IA generative agrege les donnees recentes, redige un rapport "
    "structure et propose des actions prioritaires aux gestionnaires."
)


@st.cache_resource
def get_generator():
    return ReportGenerator()


@st.cache_resource
def get_advisor():
    return ActionAdvisor()


gen = get_generator()
advisor = get_advisor()

col1, col2, col3 = st.columns([2, 1, 1], gap="medium")

with col1:
    report_type = st.selectbox(
        "Type de rapport",
        options=list(REPORT_TYPES.keys()),
        format_func=lambda key: REPORT_TYPES[key],
    )
with col2:
    start_date = st.date_input("Du", value=date.today() - timedelta(days=30))
with col3:
    end_date = st.date_input("Au", value=date.today())

col_gen, col_act, _ = st.columns([1, 1, 4])
generate = col_gen.button("Generer le rapport", type="primary")
actions_btn = col_act.button("Actions prioritaires")

if report_type in ("qualite_air", "interventions", "capteurs"):
    with st.expander("Donnees source injectees dans le prompt", expanded=False):
        try:
            from ai.context_builder import DBContextBuilder

            ctx = DBContextBuilder()
            if report_type == "qualite_air":
                st.markdown(ctx.air_quality_summary(start_date, end_date))
            elif report_type == "interventions":
                st.markdown(ctx.intervention_summary(start_date, end_date))
            else:
                st.markdown(ctx.sensor_status_summary())
        except Exception as exc:
            st.caption(f"Donnees indisponibles - {exc}")

if generate:
    with st.spinner("Generation du rapport en cours."):
        try:
            st.session_state["last_report"] = gen.generate(report_type, start_date, end_date)
            st.session_state["last_report_type"] = report_type
        except Exception as exc:
            st.error(f"Erreur lors de la generation - {exc}")

if st.session_state.get("last_report"):
    st.divider()
    title = REPORT_TYPES.get(st.session_state.get("last_report_type", ""), "Rapport")
    st.markdown(
        f'<span class="ns-tag info">{title}</span>',
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown(st.session_state["last_report"], unsafe_allow_html=False)

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        for line in st.session_state["last_report"].split("\n"):
            safe_line = line.replace("**", "").replace("##", "").replace("#", "")
            safe_line = safe_line.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 8, txt=safe_line[:100], ln=True)
        pdf_bytes = bytes(pdf.output())
        st.download_button(
            "Telecharger PDF",
            data=pdf_bytes,
            file_name=f"rapport_{st.session_state.get('last_report_type', 'neo_sousse')}.pdf",
            mime="application/pdf",
        )
    except Exception as exc:
        st.caption(f"Export PDF indisponible - {exc}")

if actions_btn:
    with st.spinner("Analyse de la situation en cours."):
        try:
            st.session_state["last_ai_actions"] = advisor.get_priority_actions()
        except Exception as exc:
            st.error(f"Erreur - {exc}")

if st.session_state.get("last_ai_actions"):
    data = st.session_state["last_ai_actions"]
    st.divider()
    st.markdown("### Actions prioritaires")

    urgence = (data.get("niveau_urgence") or "INCONNU").upper()
    urgence_class = {"VERT": "good", "ORANGE": "warn", "ROUGE": "bad"}.get(urgence, "idle")
    st.markdown(
        f'<div class="ns-badge-row"><span class="ns-tag {urgence_class}">{urgence}</span></div>',
        unsafe_allow_html=True,
    )

    if data.get("resume") and data.get("actions"):
        st.markdown(f"> {data['resume']}")
    elif data.get("resume") and not data.get("actions"):
        st.warning(data["resume"])
        if data.get("raw_output"):
            with st.expander("Sortie IA brute"):
                st.code(data["raw_output"], language="json")

    for action in data.get("actions", []):
        title = action.get("titre") or action.get("title") or "Action"
        if action.get("priorite"):
            title = f"Priorite {action['priorite']} - {title}"
        with st.expander(title):
            col_a, col_b = st.columns(2)
            col_a.markdown(f"**Description** - {action.get('description') or action.get('detail', '')}")
            if action.get("justification"):
                col_a.markdown(f"**Justification** - {action['justification']}")
            col_b.markdown(f"**Responsable** - {action.get('responsable', 'N/A')}")
            col_a.markdown(f"**Delai** - {action.get('delai_heures', '?')} h")
            col_b.markdown(f"**Impact** - {action.get('impact', action.get('detail', ''))}")
            if action.get("indicateur_succes"):
                st.markdown(f"**Indicateur de succes** - {action['indicateur_succes']}")
