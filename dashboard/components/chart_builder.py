"""Auto-selects and builds an appropriate Plotly chart from query results."""

from __future__ import annotations

import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_NEON_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0A0A0A",
    plot_bgcolor="#0A0A0A",
    font=dict(family="Roboto, sans-serif", color="#F0F0F0", size=13),
    title_font=dict(family="STIX Two Text, serif", color="#BBF351", size=16),
    colorway=["#BBF351", "#00BCFF", "#D97706", "#DC2626", "#16A34A", "#6B7280"],
    xaxis=dict(gridcolor="#2A2A2A", linecolor="#2A2A2A"),
    yaxis=dict(gridcolor="#2A2A2A", linecolor="#2A2A2A"),
    legend=dict(bgcolor="rgba(20,20,20,0.8)", bordercolor="#2A2A2A"),
    margin=dict(l=40, r=20, t=50, b=40),
)


def _neon_fig(fig):
    fig.update_layout(**_NEON_LAYOUT)
    return fig


def _normalize_col_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _is_time_col(name: str) -> bool:
    normalized = _normalize_col_name(name)
    tokens = set(filter(None, normalized.split("_")))
    if normalized.endswith(("_at", "_date", "_time", "_ts")):
        return True
    return bool(tokens & {"date", "time", "timestamp", "bucket", "heure", "jour", "mois", "annee"})


def _is_lat_col(name: str) -> bool:
    normalized = _normalize_col_name(name)
    return normalized in {"lat", "latitude"} or normalized.endswith(("_lat", "_latitude"))


def _is_lon_col(name: str) -> bool:
    normalized = _normalize_col_name(name)
    return normalized in {"lon", "lng", "long", "longitude"} or normalized.endswith(
        ("_lon", "_lng", "_long", "_longitude")
    )


def _detect_geo_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    lat_col = next((column for column in df.columns if _is_lat_col(column)), None)
    lon_col = next((column for column in df.columns if _is_lon_col(column)), None)
    return lat_col, lon_col


def _coerce_coordinates(series: pd.Series, *, axis: str) -> pd.Series:
    coords = pd.to_numeric(series, errors="coerce")
    min_value, max_value = (-90, 90) if axis == "lat" else (-180, 180)
    return coords.where(coords.between(min_value, max_value))


def auto_chart(rows: list[dict], sql: str = "") -> None:
    """Analyze columns and render the most appropriate chart type."""
    if not rows:
        return

    df = pd.DataFrame(rows)
    if df.empty:
        return

    cols = list(df.columns)
    sql_upper = (sql or "").upper()

    time_cols = [column for column in cols if _is_time_col(column)]
    numeric_cols = [column for column in cols if pd.api.types.is_numeric_dtype(df[column])]
    categorical_cols = [column for column in cols if column not in numeric_cols and column not in time_cols]
    lat_col, lon_col = _detect_geo_columns(df)

    if len(cols) == 1 and len(rows) == 1:
        st.metric("Resultat", list(rows[0].values())[0])
        return

    if lat_col and lon_col:
        map_df = df.copy()
        map_df[lat_col] = _coerce_coordinates(map_df[lat_col], axis="lat")
        map_df[lon_col] = _coerce_coordinates(map_df[lon_col], axis="lon")
        map_df = map_df.dropna(subset=[lat_col, lon_col])
        if not map_df.empty:
            color_col = next((column for column in numeric_cols if column not in {lat_col, lon_col}), None)
            fig = px.scatter_mapbox(
                map_df,
                lat=lat_col,
                lon=lon_col,
                color=color_col,
                hover_data=cols,
                mapbox_style="carto-darkmatter",
                center={
                    "lat": float(map_df[lat_col].mean()),
                    "lon": float(map_df[lon_col].mean()),
                },
                zoom=11,
                height=420,
                title="Carte des resultats",
                color_continuous_scale=[[0, "#00BCFF"], [1, "#BBF351"]],
            )
            fig.update_layout(mapbox=dict(style="carto-darkmatter"))
            st.plotly_chart(_neon_fig(fig), use_container_width=True)
            return

    if time_cols and numeric_cols:
        x_col = time_cols[0]
        y_col = next((column for column in numeric_cols if column not in {lat_col, lon_col}), numeric_cols[0])
        try:
            df[x_col] = pd.to_datetime(df[x_col])
            df = df.sort_values(x_col)
        except Exception:
            pass
        else:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=f"Evolution de {y_col} dans le temps",
                labels={x_col: "Date / heure", y_col: y_col},
                color_discrete_sequence=["#00BCFF"],
            )
            fig.update_layout(hovermode="x unified")
            fig.add_hline(
                y=float(df[y_col].mean()),
                line_dash="dot",
                line_color="#BBF351",
                annotation_text=f"Moyenne : {df[y_col].mean():.2f}",
            )
            st.plotly_chart(_neon_fig(fig), use_container_width=True)
            return

    if categorical_cols and numeric_cols and "GROUP BY" in sql_upper:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        df_sorted = df.sort_values(y_col, ascending=False)
        fig = px.bar(
            df_sorted,
            x=x_col,
            y=y_col,
            title=f"{y_col} par {x_col}",
            color=y_col,
            color_continuous_scale=[[0, "#00BCFF"], [1, "#BBF351"]],
        )
        st.plotly_chart(_neon_fig(fig), use_container_width=True)
        return

    if "AVG" in sql_upper and len(rows) == 1 and numeric_cols:
        value = float(df[numeric_cols[0]].iloc[0])
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                title={"text": numeric_cols[0], "font": {"color": "#9CA3AF"}},
                number={"font": {"color": "#BBF351"}},
                gauge={
                    "axis": {"range": [0, max(100, value * 1.5)], "tickcolor": "#9CA3AF"},
                    "bar": {"color": "#BBF351"},
                    "bgcolor": "#141414",
                    "bordercolor": "#2A2A2A",
                },
            )
        )
        st.plotly_chart(_neon_fig(fig), use_container_width=True)
        return

    if categorical_cols and numeric_cols:
        fig = px.bar(
            df,
            x=categorical_cols[0],
            y=numeric_cols[0],
            color_discrete_sequence=["#BBF351"],
        )
        st.plotly_chart(_neon_fig(fig), use_container_width=True)
        return

    st.dataframe(df, use_container_width=True)
