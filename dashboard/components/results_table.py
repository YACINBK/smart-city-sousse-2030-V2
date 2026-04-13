"""Paginated dataframe component."""

import streamlit as st
import pandas as pd


def show_results_table(rows: list[dict], page_size: int = 25, key: str = "table") -> None:
    if not rows:
        st.info("Aucun résultat.")
        return

    df = pd.DataFrame(rows)
    total = len(df)

    if total <= page_size:
        st.dataframe(df, use_container_width=True)
        st.caption(f"{total} résultat(s)")
        return

    # Pagination
    pages = (total - 1) // page_size + 1
    page = st.number_input(f"Page (1–{pages})", min_value=1, max_value=pages,
                           value=1, key=f"{key}_page")
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    st.dataframe(df.iloc[start:end], use_container_width=True)
    st.caption(f"Affichage {start+1}–{end} sur {total} résultats")
