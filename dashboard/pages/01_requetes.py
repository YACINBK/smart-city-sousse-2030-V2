"""Requetes en langage naturel: saisie, compilation, execution et visualisation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from dashboard import state as S
from dashboard.components.ast_viewer import show_debug_pipeline
from dashboard.components.chart_builder import auto_chart
from dashboard.components.results_table import show_results_table
from dashboard.theme import apply_theme

st.set_page_config(page_title="Requetes - Neo-Sousse 2030", layout="wide")
apply_theme()

st.markdown("# Requetes en langage naturel")
st.caption(
    "Posez une question en francais : le compilateur produit la requete SQL, "
    "l'execute, puis presente les resultats."
)


for key in (
    S.LAST_SQL,
    S.LAST_AST,
    S.LAST_TOKENS,
    S.QUERY_RESULTS,
    S.AMBIGUITY_QUESTION,
    S.AMBIGUITY_INTERPRETATIONS,
    S.SQL_NL_EXPLANATION,
    S.QUERY_DESCRIPTION,
):
    st.session_state.setdefault(key, None)
st.session_state.setdefault(S.DEBUG_MODE, False)


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


def _store_query_output(
    sql: str,
    params: dict | None = None,
    ast: dict | None = None,
    tokens: list | None = None,
    description: str | None = None,
) -> None:
    st.session_state[S.LAST_SQL] = sql
    st.session_state[S.LAST_SQL_PARAMS] = params or {}
    st.session_state[S.LAST_AST] = ast
    st.session_state[S.LAST_TOKENS] = tokens or []
    st.session_state[S.QUERY_DESCRIPTION] = description

    try:
        st.session_state[S.SQL_NL_EXPLANATION] = report_gen.explain_sql(sql)
    except Exception:
        st.session_state[S.SQL_NL_EXPLANATION] = None

    try:
        from database.connection import execute_query

        st.session_state[S.QUERY_RESULTS] = execute_query(sql, params or {})
    except Exception as exc:
        st.error(f"Erreur d'execution SQL - {exc}")
        st.session_state[S.QUERY_RESULTS] = None


with st.sidebar:
    st.markdown("### Exemples")
    examples = [
        "Affiche les 5 zones les plus polluees",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score ecologique > 80 ?",
        "Donne-moi le trajet le plus economique en CO2",
        "Affiche les interventions avec priorite urgente",
        "Combien d'interventions sont en cours ?",
        "Moyenne du pm25 des capteurs actifs",
        "Affiche les capteurs dont le statut est hors_service",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:24]}", use_container_width=True):
            st.session_state[S.QUERY_INPUT] = ex
            st.rerun()

    st.divider()
    st.session_state[S.DEBUG_MODE] = st.toggle(
        "Mode debogage",
        value=st.session_state[S.DEBUG_MODE],
        help="Affiche les tokens, l'AST et le SQL cote a cote.",
    )


st.markdown(
    '<span class="ns-card-title">Question en langage naturel</span>',
    unsafe_allow_html=True,
)
query = st.text_input(
    "Votre question",
    value=st.session_state.get(S.QUERY_INPUT, ""),
    placeholder="Affiche les 5 zones les plus polluees",
    key=S.QUERY_INPUT,
    label_visibility="collapsed",
)

col_a, col_b, _ = st.columns([1, 1, 6])
submitted = col_a.button("Compiler", type="primary")
if col_b.button("Effacer"):
    for key in (
        S.LAST_SQL,
        S.LAST_AST,
        S.LAST_TOKENS,
        S.QUERY_RESULTS,
        S.AMBIGUITY_QUESTION,
        S.AMBIGUITY_INTERPRETATIONS,
        S.SQL_NL_EXPLANATION,
        S.LAST_SQL_PARAMS,
        S.QUERY_DESCRIPTION,
    ):
        st.session_state[key] = None
    st.rerun()


if st.session_state[S.AMBIGUITY_QUESTION]:
    st.warning(f"Ambiguite detectee - {st.session_state[S.AMBIGUITY_QUESTION]}")
    interps = st.session_state[S.AMBIGUITY_INTERPRETATIONS] or []
    chosen = st.radio(
        "Interpretations possibles",
        options=[f"Option {i + 1}" for i in range(len(interps))],
        captions=[sql.splitlines()[0][:80] + "..." for sql in interps],
        key="ambiguity_choice",
    )
    if st.button("Retenir cette interpretation", type="primary"):
        idx = int(chosen.split()[-1]) - 1
        selected_sql = interps[idx]
        st.session_state[S.AMBIGUITY_QUESTION] = None
        st.session_state[S.AMBIGUITY_INTERPRETATIONS] = None
        _store_query_output(
            selected_sql,
            params={},
            ast=None,
            tokens=None,
            description="Interpretation selectionnee apres levee d'ambiguite.",
        )
        st.rerun()


if submitted and query:
    result = pipeline.compile_safe(query)

    if result.get("ambiguous"):
        st.session_state[S.AMBIGUITY_QUESTION] = result.get("question")
        st.session_state[S.AMBIGUITY_INTERPRETATIONS] = result.get("interpretations", [])
        st.session_state[S.LAST_SQL] = None
        st.session_state[S.QUERY_RESULTS] = None
        st.rerun()
    elif not result["success"]:
        st.error(f"Erreur de compilation - {result['error']}")
        st.session_state[S.LAST_SQL] = None
    else:
        _store_query_output(
            result["sql"],
            params=result.get("params", {}),
            ast=result.get("ast"),
            tokens=result.get("tokens", []),
            description=result.get("description"),
        )


if st.session_state[S.LAST_SQL]:
    st.divider()

    if st.session_state.get(S.SQL_NL_EXPLANATION):
        st.markdown(f"> {st.session_state[S.SQL_NL_EXPLANATION]}")

    if st.session_state.get(S.QUERY_DESCRIPTION):
        st.caption(st.session_state[S.QUERY_DESCRIPTION])

    st.markdown(
        '<span class="ns-tag info">SQL genere</span>',
        unsafe_allow_html=True,
    )
    with st.expander("Requete SQL generee", expanded=True):
        st.code(st.session_state[S.LAST_SQL], language="sql")

    results = st.session_state[S.QUERY_RESULTS]
    if results is not None:
        st.markdown(f"#### Resultats - {len(results)} ligne(s)")
        tab_chart, tab_table = st.tabs(["Visualisation", "Tableau"])
        with tab_chart:
            try:
                auto_chart(results, st.session_state[S.LAST_SQL])
            except Exception as exc:
                st.warning(f"Visualisation indisponible - {exc}")
                show_results_table(results)
        with tab_table:
            show_results_table(results)

    if st.session_state[S.DEBUG_MODE] and st.session_state[S.LAST_AST]:
        show_debug_pipeline(
            tokens=st.session_state[S.LAST_TOKENS] or [],
            ast_dict=st.session_state[S.LAST_AST],
            sql=st.session_state[S.LAST_SQL],
        )
