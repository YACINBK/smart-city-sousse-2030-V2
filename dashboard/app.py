"""
Neo-Sousse 2030 — Smart City Dashboard
Streamlit multi-page app entry point.

Initializes shared resources once with st.cache_resource.
"""

import streamlit as st
import sys
import os

# Ensure project root is on sys.path regardless of launch directory
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

st.set_page_config(
    page_title="Neo-Sousse 2030",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_pipeline():
    from compiler.pipeline import NLToSQLPipeline
    return NLToSQLPipeline()


@st.cache_resource
def get_report_generator():
    from ai.report_generator import ReportGenerator
    return ReportGenerator()


@st.cache_resource
def get_action_advisor():
    from ai.action_advisor import ActionAdvisor
    return ActionAdvisor()


@st.cache_resource
def get_fsm_repo():
    from fsm.persistence import FSMStateRepository
    return FSMStateRepository()


@st.cache_resource
def get_visualizer():
    from fsm.visualizer import GraphvizVisualizer
    return GraphvizVisualizer()


# ── Sidebar navigation ────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=Neo-Sousse+2030", use_container_width=True)
    st.markdown("## 🏙️ Neo-Sousse 2030")
    st.markdown("*Plateforme Intelligente de Gestion Urbaine*")
    st.divider()

    try:
        from database.connection import test_connection
        db_ok = test_connection()
        st.success("✅ Base de données connectée") if db_ok else st.error("❌ DB déconnectée")
    except Exception:
        st.warning("⚠️ DB non disponible")

    st.divider()
    st.caption("Module : Théorie des Langages et Compilation")
    st.caption("Section IA 2 — 2025-2026")


# ── Home page ─────────────────────────────────────────────────
st.title("🏙️ Neo-Sousse 2030 — Plateforme Smart City")
st.markdown(
    """
    Bienvenue sur la plateforme intelligente de gestion des données urbaines de **Neo-Sousse 2030**.

    | Module | Description |
    |--------|-------------|
    | 🔍 **Requêtes NL** | Interrogez la base en français naturel |
    | 🔄 **Automates** | Visualisez et contrôlez les workflows métier |
    | 🤖 **Rapports IA** | Générez des rapports analytiques automatiquement |
    | 📊 **Données** | Explorez les données brutes et séries temporelles |

    Utilisez le menu à gauche pour naviguer entre les modules.
    """
)

# Quick stats
st.divider()
st.subheader("Tableau de bord rapide")
try:
    from database.connection import execute_query
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        r = execute_query("SELECT COUNT(*) AS n FROM capteurs WHERE statut='ACTIF'")
        st.metric("Capteurs actifs", r[0]["n"] if r else "—")
    with col2:
        r = execute_query("SELECT COUNT(*) AS n FROM capteurs WHERE statut='HORS_SERVICE'")
        st.metric("Hors service", r[0]["n"] if r else "—", delta_color="inverse")
    with col3:
        r = execute_query("SELECT COUNT(*) AS n FROM interventions WHERE statut != 'TERMINÉ'")
        st.metric("Interventions en cours", r[0]["n"] if r else "—")
    with col4:
        r = execute_query("SELECT COUNT(*) AS n FROM alertes WHERE resolved=FALSE AND severity='CRITICAL'")
        st.metric("Alertes critiques", r[0]["n"] if r else "—", delta_color="inverse")
except Exception:
    st.info("Connectez la base de données pour voir les statistiques en temps réel.")
