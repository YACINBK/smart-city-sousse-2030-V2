"""
Page 4 — Explorateur de Données

Features:
  - Entity table browser
  - TimescaleDB time-bucket line chart for mesures
  - Sensor filter by zone / type / status
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from database.connection import execute_query
from dashboard.components.results_table import show_results_table

st.set_page_config(page_title="Données — Neo-Sousse 2030", page_icon="📊", layout="wide")
st.title("📊 Explorateur de Données")

tab1, tab2, tab3, tab4 = st.tabs(["Capteurs", "Mesures (TimescaleDB)", "Interventions", "Citoyens"])

with tab1:
    st.subheader("Réseau de Capteurs")
    try:
        col1, col2 = st.columns(2)
        zones = execute_query("SELECT nom FROM zones ORDER BY nom")
        zone_names = ["Toutes"] + [z["nom"] for z in zones]
        selected_zone = col1.selectbox("Zone", zone_names, key="zone_filter")
        statuts = ["Tous", "ACTIF", "INACTIF", "SIGNALÉ", "EN_MAINTENANCE", "HORS_SERVICE"]
        selected_statut = col2.selectbox("Statut", statuts, key="statut_filter")

        sql = """
            SELECT c.id, c.nom, c.type, z.nom AS zone, c.statut,
                   c.fabricant, c.date_installation::date AS installation
            FROM capteurs c LEFT JOIN zones z ON z.id=c.zone_id
            WHERE 1=1
        """
        params = {}
        if selected_zone != "Toutes":
            sql += " AND z.nom=:zone"
            params["zone"] = selected_zone
        if selected_statut != "Tous":
            sql += " AND c.statut=:statut"
            params["statut"] = selected_statut
        sql += " ORDER BY c.id"

        rows = execute_query(sql, params)
        show_results_table(rows, key="capteurs_table")
    except Exception as e:
        st.error(f"Erreur : {e}")

with tab2:
    st.subheader("Séries Temporelles — Mesures (TimescaleDB)")
    try:
        col1, col2, col3 = st.columns(3)
        capteurs = execute_query("SELECT id, nom FROM capteurs WHERE statut='ACTIF' ORDER BY nom")
        if capteurs:
            cap_options = {f"{c['nom']} (ID {c['id']})": c["id"] for c in capteurs}
            selected_cap_name = col1.selectbox("Capteur", list(cap_options.keys()))
            cap_id = cap_options[selected_cap_name]

            metric = col2.selectbox("Mesure", ["pm25", "pm10", "temperature", "humidite", "co2", "no2"])
            days = col3.slider("Jours", min_value=1, max_value=90, value=7)

            rows = execute_query(
                """
                SELECT
                    time_bucket('1 hour', mesure_at) AS heure,
                    ROUND(AVG(:metric)::numeric, 2) AS valeur
                FROM mesures
                WHERE capteur_id=:id AND mesure_at > NOW() - (:days || ' days')::INTERVAL
                  AND :metric IS NOT NULL
                GROUP BY heure ORDER BY heure
                """.replace(":metric", metric),
                {"id": cap_id, "days": days},
            )
            if rows:
                df = pd.DataFrame(rows)
                df["heure"] = pd.to_datetime(df["heure"])
                fig = px.line(
                    df, x="heure", y="valeur",
                    title=f"{metric.upper()} — {selected_cap_name} (derniers {days} jours)",
                    labels={"heure": "Date/Heure", "valeur": metric},
                )
                fig.add_hline(y=df["valeur"].mean(), line_dash="dot",
                              annotation_text=f"Moy: {df['valeur'].mean():.1f}")
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"{len(rows)} points de données | Min: {df['valeur'].min():.2f} | "
                           f"Max: {df['valeur'].max():.2f} | Moy: {df['valeur'].mean():.2f}")
            else:
                st.info("Aucune donnée pour cette période.")
        else:
            st.info("Aucun capteur actif.")
    except Exception as e:
        st.error(f"Erreur TimescaleDB : {e}")

with tab3:
    st.subheader("Interventions")
    try:
        rows = execute_query(
            """SELECT i.id, c.nom AS capteur, i.statut, i.priorite, i.description,
                      i.created_at::date AS date_creation,
                      CASE WHEN i.ai_validation IS NOT NULL
                           THEN (i.ai_validation->>'approved')::boolean ELSE NULL END AS ia_approuvee
               FROM interventions i JOIN capteurs c ON c.id=i.capteur_id
               ORDER BY i.created_at DESC LIMIT 100"""
        )
        show_results_table(rows, key="inter_table")
    except Exception as e:
        st.error(f"Erreur : {e}")

with tab4:
    st.subheader("Citoyens")
    try:
        rows = execute_query(
            """SELECT c.nom, c.prenom, z.nom AS zone, c.score_ecolo
               FROM citoyens c LEFT JOIN zones z ON z.id=c.zone_id
               ORDER BY c.score_ecolo DESC LIMIT 100"""
        )
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        if not df.empty:
            fig = px.histogram(df, x="score_ecolo", nbins=20,
                               title="Distribution des scores écologiques",
                               labels={"score_ecolo": "Score Écologique"})
            st.plotly_chart(fig, use_container_width=True)
        show_results_table(rows, key="citoyens_table")
    except Exception as e:
        st.error(f"Erreur : {e}")
