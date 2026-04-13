"""Debug: renders the AST as an expandable JSON tree and token list."""

import streamlit as st
from compiler.tokens import Token


def show_debug_pipeline(tokens: list, ast_dict: dict, sql: str) -> None:
    """Visual stepper: tokens → AST → SQL."""
    st.markdown("---")
    st.markdown("### 🔬 Mode Débogage — Pipeline de Compilation")

    cols = st.columns(3)

    with cols[0]:
        st.markdown("**① Tokens (Lexer)**")
        for tok in tokens:
            if tok["type"] != "EOF":
                color = "#e8f4f8" if tok["type"] not in ("IDENTIFIER",) else "#fff3cd"
                st.markdown(
                    f'<span style="background:{color};padding:2px 6px;border-radius:4px;'
                    f'font-size:0.8em;margin:2px;display:inline-block;">'
                    f'<b>{tok["type"]}</b>: {tok["value"]}</span>',
                    unsafe_allow_html=True,
                )

    with cols[1]:
        st.markdown("**② AST (Parser)**")
        st.json(ast_dict, expanded=2)

    with cols[2]:
        st.markdown("**③ SQL Généré**")
        st.code(sql, language="sql")
