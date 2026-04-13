"""
Page 3 — Rapports IA Génératifs

Features:
  - Report type selector
  - Date range picker
  - DB context data preview (expandable)
  - LLM-generated report in Markdown
  - Priority actions (JSON formatted nicely)
  - PDF export (bonus)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from datetime import date, timedelta
from ai.report_generator import ReportGenerator, REPORT_TYPES
from ai.action_advisor import ActionAdvisor

st.set_page_config(page_title="Rapports IA — Neo-Sousse 2030", page_icon="🤖", layout="wide")
st.title("🤖 Rapports Analytiques par IA")

@st.cache_resource
def get_generator():
    return ReportGenerator()

@st.cache_resource
def get_advisor():
    return ActionAdvisor()

gen = get_generator()
advisor = get_advisor()

# ── Controls ──────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    report_type = st.selectbox(
        "Type de rapport",
        options=list(REPORT_TYPES.keys()),
        format_func=lambda k: REPORT_TYPES[k],
    )

with col2:
    start_date = st.date_input("Du", value=date.today() - timedelta(days=30))

with col3:
    end_date = st.date_input("Au", value=date.today())

col_gen, col_act = st.columns([1, 1])
generate = col_gen.button("📄 Générer le rapport", type="primary")
actions_btn = col_act.button("⚡ Actions prioritaires IA")

# ── DB Context preview ────────────────────────────────────────
if report_type in ("qualite_air", "interventions", "capteurs"):
    with st.expander("📊 Données source (contexte injecté dans le prompt)", expanded=False):
        try:
            from ai.context_builder import DBContextBuilder
            ctx = DBContextBuilder()
            if report_type == "qualite_air":
                st.markdown(ctx.air_quality_summary(start_date, end_date))
            elif report_type == "interventions":
                st.markdown(ctx.intervention_summary(start_date, end_date))
            elif report_type == "capteurs":
                st.markdown(ctx.sensor_status_summary())
        except Exception as e:
            st.warning(f"Données indisponibles : {e}")

# ── Report generation ─────────────────────────────────────────
if generate:
    with st.spinner("⏳ Génération du rapport en cours..."):
        try:
            report = gen.generate(report_type, start_date, end_date)
            st.session_state["last_report"] = report
            st.session_state["last_report_type"] = report_type
        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")

if "last_report" in st.session_state and st.session_state["last_report"]:
    st.divider()
    st.subheader(f"📋 {REPORT_TYPES.get(st.session_state.get('last_report_type', ''), 'Rapport')}")
    st.markdown(st.session_state["last_report"])

    # PDF export (bonus)
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        for line in st.session_state["last_report"].split("\n"):
            clean = line.replace("**", "").replace("##", "").replace("#", "")
            pdf.cell(0, 8, clean.encode("latin-1", "replace").decode("latin-1"), ln=True)
        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        st.download_button(
            "⬇ Télécharger PDF",
            data=pdf_bytes,
            file_name=f"rapport_{st.session_state.get('last_report_type','')}.pdf",
            mime="application/pdf",
        )
    except Exception:
        pass

# ── Priority actions ──────────────────────────────────────────
if actions_btn:
    with st.spinner("⏳ Analyse de la situation en cours..."):
        try:
            result = advisor.get_priority_actions()
            st.session_state["last_ai_actions"] = result
        except Exception as e:
            st.error(f"Erreur : {e}")

if "last_ai_actions" in st.session_state and st.session_state["last_ai_actions"]:
    data = st.session_state["last_ai_actions"]
    st.divider()
    st.subheader("⚡ Actions Prioritaires")

    urgence = data.get("niveau_urgence", "?")
    color_map = {"VERT": "success", "ORANGE": "warning", "ROUGE": "error"}
    getattr(st, color_map.get(urgence, "info"))(f"Niveau d'urgence global : **{urgence}**")

    if data.get("resume"):
        st.markdown(f"*{data['resume']}*")

    for action in data.get("actions", []):
        with st.expander(f"Priorité {action.get('priorite', '?')} — {action.get('titre', '')}"):
            col_a, col_b = st.columns(2)
            col_a.markdown(f"**Description** : {action.get('description', '')}")
            col_b.markdown(f"**Responsable** : {action.get('responsable', '')}")
            col_a.markdown(f"**Délai** : {action.get('delai_heures', '?')}h")
            col_b.markdown(f"**Impact** : {action.get('impact', '')}")
