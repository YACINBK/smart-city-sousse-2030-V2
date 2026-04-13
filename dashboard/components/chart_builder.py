"""Auto-selects and builds appropriate Plotly chart from query results."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st


def auto_chart(rows: list[dict], sql: str = "") -> None:
    """Analyze columns and render the most appropriate chart type."""
    if not rows:
        return

    df = pd.DataFrame(rows)
    cols = list(df.columns)
    sql_upper = sql.upper()

    # Try to detect chart type from query structure and column names
    time_cols = [c for c in cols if any(k in c.lower() for k in ("at", "date", "time", "bucket"))]
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in cols if c not in numeric_cols and c not in time_cols]
    geo_cols = [c for c in cols if "lat" in c.lower() or "lon" in c.lower()]

    # COUNT(*) single value → metric
    if len(cols) == 1 and len(rows) == 1:
        st.metric("Résultat", list(rows[0].values())[0])
        return

    # Time series
    if time_cols and numeric_cols:
        x_col = time_cols[0]
        y_col = numeric_cols[0]
        try:
            df[x_col] = pd.to_datetime(df[x_col])
            df = df.sort_values(x_col)
            fig = px.line(df, x=x_col, y=y_col,
                          title=f"Évolution de {y_col} dans le temps",
                          labels={x_col: "Date/Heure", y_col: y_col})
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass
        return

    # GROUP BY → bar chart
    if categorical_cols and numeric_cols and "GROUP BY" in sql_upper:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        df_sorted = df.sort_values(y_col, ascending=False)
        fig = px.bar(df_sorted, x=x_col, y=y_col,
                     title=f"{y_col} par {x_col}",
                     color=y_col,
                     color_continuous_scale="RdYlGn_r")
        st.plotly_chart(fig, use_container_width=True)
        return

    # Geo scatter
    if len(geo_cols) >= 2:
        lat_col = next(c for c in geo_cols if "lat" in c.lower())
        lon_col = next(c for c in geo_cols if "lon" in c.lower())
        color_col = numeric_cols[0] if numeric_cols else None
        fig = px.scatter_mapbox(
            df, lat=lat_col, lon=lon_col, color=color_col,
            hover_data=cols,
            mapbox_style="open-street-map",
            zoom=12, height=400,
            title="Carte des résultats",
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    # AVG single value → gauge
    if "AVG" in sql_upper and len(rows) == 1 and numeric_cols:
        val = float(df[numeric_cols[0]].iloc[0])
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            title={"text": numeric_cols[0]},
            gauge={"axis": {"range": [0, max(100, val * 1.5)]},
                   "bar": {"color": "royalblue"}},
        ))
        st.plotly_chart(fig, use_container_width=True)
        return

    # Fallback: simple bar if has categorical + numeric
    if categorical_cols and numeric_cols:
        fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0])
        st.plotly_chart(fig, use_container_width=True)
