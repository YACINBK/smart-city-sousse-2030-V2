"""
Page 1 — Requêtes en Langage Naturel → SQL

Features:
  - NL input box with example queries
  - Ambiguity detection + follow-up question
  - SQL display + SQL→NL back-translation
  - Results table + auto-selected chart
  - Mode Débogage: token → AST → SQL stepper
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from dashboard import state as S
from dashboard.components.results_table import show_results_table
from dashboard.components.chart_builder import auto_chart
from dashboard.components.ast_viewer import show_debug_pipeline

st.set_page_config(page_title="Requêtes NL — Neo-Sousse 2030", page_icon="🔍", layout="wide")
st.title("🔍 Requêtes en Langage Naturel")

# ── Init session state ────────────────────────────────────────
for key in [S.LAST_SQL, S.LAST_AST, S.LAST_TOKENS, S.QUERY_RESULTS,
            S.AMBIGUITY_QUESTION, S.AMBIGUITY_INTERPRETATIONS,
            S.SQL_NL_EXPLANATION, S.QUERY_DESCRIPTION]:
    if key not in st.session_state:
        st.session_state[key] = None

if S.DEBUG_MODE not in st.session_state:
    st.session_state[S.DEBUG_MODE] = False

# ── Pipeline setup ────────────────────────────────────────────
@st.cache_resource
def get_pipeline():
    from compiler.pipeline import NLToSQLPipeline
    return NLToSQLPipeline()

@st.cache_resource
def get_report_gen():
    from ai.report_generator import ReportGenerator
    return ReportGenerator()

pipeline = get_pipeline()
report_gen = get_report_gen()

# ── Sidebar examples ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### Exemples de requêtes")
    examples = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
        "Donne-moi le trajet le plus économique en CO2",
        "Affiche les interventions avec priorité urgente",
        "Combien d'interventions sont en cours ?",
        "Moyenne du pm25 des capteurs actifs",
        "Affiche les capteurs dont le statut est hors_service",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}"):
            st.session_state[S.QUERY_INPUT] = ex
            st.rerun()

    st.divider()
    st.session_state[S.DEBUG_MODE] = st.toggle("🔬 Mode Débogage",
                                                value=st.session_state[S.DEBUG_MODE])

# ── Main input ────────────────────────────────────────────────
query = st.text_input(
    "Saisissez votre requête en français :",
    value=st.session_state.get(S.QUERY_INPUT, ""),
    placeholder="Ex: Affiche les 5 zones les plus polluées",
    key=S.QUERY_INPUT,
)

col_submit, col_clear = st.columns([1, 5])
submitted = col_submit.button("🚀 Soumettre", type="primary")
if col_clear.button("🗑 Effacer"):
    for key in [S.LAST_SQL, S.LAST_AST, S.LAST_TOKENS, S.QUERY_RESULTS,
                S.AMBIGUITY_QUESTION, S.AMBIGUITY_INTERPRETATIONS, S.SQL_NL_EXPLANATION]:
        st.session_state[key] = None
    st.rerun()

# ── Ambiguity follow-up ────────────────────────────────────────
if st.session_state[S.AMBIGUITY_QUESTION]:
    st.warning(f"⚠️ **Ambiguïté détectée** : {st.session_state[S.AMBIGUITY_QUESTION]}")
    interps = st.session_state[S.AMBIGUITY_INTERPRETATIONS] or []
    chosen_sql = st.radio(
        "Choisissez une interprétation :",
        options=[f"Option {i+1}" for i in range(len(interps))],
        captions=[sql.splitlines()[0][:80] + "..." for sql in interps],
        key="ambiguity_choice",
    )
    if st.button("✅ Utiliser cette interprétation"):
        idx = int(chosen_sql.split()[-1]) - 1
        st.session_state[S.LAST_SQL] = interps[idx]
        st.session_state[S.AMBIGUITY_QUESTION] = None
        st.session_state[S.AMBIGUITY_INTERPRETATIONS] = None
        submitted = True  # trigger execution

# ── Compile & execute ─────────────────────────────────────────
if submitted and query:
    result = pipeline.compile_safe(query)

    if result.get("ambiguous"):
        st.session_state[S.AMBIGUITY_QUESTION] = result.get("question")
        st.session_state[S.AMBIGUITY_INTERPRETATIONS] = result.get("interpretations", [])
        st.session_state[S.LAST_SQL] = None
        st.session_state[S.QUERY_RESULTS] = None
        st.rerun()

    elif not result["success"]:
        st.error(f"❌ Erreur de compilation : {result['error']}")
        st.session_state[S.LAST_SQL] = None

    else:
        sql = result["sql"]
        st.session_state[S.LAST_SQL] = sql
        st.session_state[S.LAST_SQL_PARAMS] = result.get("params", {})
        st.session_state[S.LAST_AST] = result.get("ast")
        st.session_state[S.LAST_TOKENS] = result.get("tokens", [])
        st.session_state[S.QUERY_DESCRIPTION] = result.get("description")

        # SQL → NL back-translation
        try:
            explanation = report_gen.explain_sql(sql)
            st.session_state[S.SQL_NL_EXPLANATION] = explanation
        except Exception:
            st.session_state[S.SQL_NL_EXPLANATION] = None

        # Execute SQL
        try:
            from database.connection import execute_query
            rows = execute_query(sql, result.get("params", {}))
            st.session_state[S.QUERY_RESULTS] = rows
        except Exception as e:
            st.error(f"❌ Erreur d'exécution SQL : {e}")
            st.session_state[S.QUERY_RESULTS] = None

# ── Display results ───────────────────────────────────────────
if st.session_state[S.LAST_SQL]:
    # SQL→NL explanation banner
    if st.session_state.get(S.SQL_NL_EXPLANATION):
        st.info(f"💡 {st.session_state[S.SQL_NL_EXPLANATION]}")

    if st.session_state.get(S.QUERY_DESCRIPTION):
        st.caption(st.session_state[S.QUERY_DESCRIPTION])

    with st.expander("📋 Requête SQL générée", expanded=True):
        st.code(st.session_state[S.LAST_SQL], language="sql")

    results = st.session_state[S.QUERY_RESULTS]
    if results is not None:
        st.subheader(f"Résultats ({len(results)} ligne(s))")
        tab1, tab2 = st.tabs(["📊 Visualisation", "📋 Tableau"])
        with tab1:
            auto_chart(results, st.session_state[S.LAST_SQL])
        with tab2:
            show_results_table(results)

    # Debug mode stepper
    if st.session_state[S.DEBUG_MODE] and st.session_state[S.LAST_AST]:
        show_debug_pipeline(
            tokens=st.session_state[S.LAST_TOKENS] or [],
            ast_dict=st.session_state[S.LAST_AST],
            sql=st.session_state[S.LAST_SQL],
        )
