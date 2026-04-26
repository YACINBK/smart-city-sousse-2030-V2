"""Pytest fixtures for unit tests and scenario tests."""

import os
import sys

import pytest

from config.settings import get_settings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("USE_MOCK_LLM", "true")
os.environ.setdefault("DATABASE_URL", "postgresql://neo_user:neo_password@localhost:5432/neo_sousse")
os.environ.setdefault("HORS_SERVICE_ALERT_DELAY_SECONDS", "30")

_MOCK_ZONES = [
    {
        "id": 1,
        "nom": "Medina de Sousse",
        "description": "Centre historique",
        "geom_lat": 35.8254,
        "geom_lon": 10.6370,
        "superficie": 4.1,
    },
    {
        "id": 2,
        "nom": "Zone industrielle de Sidi Abdelhamid",
        "description": "Secteur industriel",
        "geom_lat": 35.8053,
        "geom_lon": 10.6407,
        "superficie": 9.2,
    },
]
_MOCK_CAPTEURS = [
    {"id": 1, "nom": "CAP-AIR-001", "type": "qualite_air", "zone_id": 1, "statut": "ACTIF", "fabricant": "UrbanSense"},
    {"id": 2, "nom": "CAP-AIR-002", "type": "qualite_air", "zone_id": 2, "statut": "HORS_SERVICE", "fabricant": "UrbanSense"},
    {"id": 3, "nom": "CAP-TRAF-003", "type": "trafic", "zone_id": 1, "statut": "SIGNALÉ", "fabricant": "SensorTech"},
]
_MOCK_INTERVENTIONS = [
    {"id": 10, "capteur_id": 2, "statut": "DEMANDE", "priorite": "URGENTE"},
    {"id": 11, "capteur_id": 3, "statut": "TECH1_ASSIGNÉ", "priorite": "HAUTE"},
    {"id": 12, "capteur_id": 1, "statut": "TERMINÉ", "priorite": "NORMALE"},
]
_MOCK_CITOYENS = [
    {"id": 1, "nom": "Ben Ali", "prenom": "Nour", "zone_id": 1, "score_ecolo": 82.4},
    {"id": 2, "nom": "Trabelsi", "prenom": "Karim", "zone_id": 2, "score_ecolo": 67.1},
]
_MOCK_VEHICULES = [
    {"id": 1, "immatriculation": "TN-1001-NS", "type": "bus", "zone_id": 1, "statut": "STATIONNÉ"},
    {"id": 2, "immatriculation": "TN-1002-NS", "type": "utilitaire", "zone_id": 2, "statut": "EN_PANNE"},
]
_MOCK_ALERTES = [
    {"id": 1, "severity": "CRITICAL", "resolved": False},
    {"id": 2, "severity": "WARNING", "resolved": False},
]
_MOCK_MESURES = [
    {"zone": "Medina de Sousse", "avg_pm25": 24.4, "avg_pm10": 37.8, "max_pm25": 45.2, "nb_mesures": 240},
    {
        "zone": "Zone industrielle de Sidi Abdelhamid",
        "avg_pm25": 39.6,
        "avg_pm10": 58.7,
        "max_pm25": 71.1,
        "nb_mesures": 260,
    },
]


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.lower().split())


def _mock_execute_query(sql: str, params: dict | None = None) -> list[dict]:
    normalized = _normalize_sql(sql)

    if normalized.startswith("insert ") or normalized.startswith("update ") or normalized.startswith("delete "):
        return []

    if "from zones" in normalized and "count(*) as n" in normalized:
        return [{"n": len(_MOCK_ZONES)}]
    if normalized == "select nom from zones order by nom":
        return [{"nom": row["nom"]} for row in _MOCK_ZONES]
    if normalized == "select id from zones order by id":
        return [{"id": row["id"]} for row in _MOCK_ZONES]

    if "from techniciens" in normalized and "count(*) as n" in normalized:
        return [{"n": 2}]
    if normalized == "select id from techniciens":
        return [{"id": 1}, {"id": 2}]

    if "from capteurs" in normalized and "count(*) as n" in normalized:
        if "statut='actif'" in normalized:
            return [{"n": 1}]
        if "statut='hors_service'" in normalized:
            return [{"n": 1}]
        return [{"n": len(_MOCK_CAPTEURS)}]
    if "from capteurs" in normalized and "group by statut" in normalized:
        return [
            {"statut": "ACTIF", "total": 1},
            {"statut": "HORS_SERVICE", "total": 1},
            {"statut": "SIGNALÉ", "total": 1},
        ]
    if "from capteurs" in normalized and "where statut='actif'" in normalized and "select id, nom" in normalized:
        return [{"id": 1, "nom": "CAP-AIR-001"}]
    if "from capteurs" in normalized and "left join zones" in normalized:
        return [
            {
                "id": row["id"],
                "nom": row["nom"],
                "type": row["type"],
                "zone": next(zone["nom"] for zone in _MOCK_ZONES if zone["id"] == row["zone_id"]),
                "statut": row["statut"],
                "fabricant": row["fabricant"],
                "installation": "2025-10-01",
            }
            for row in _MOCK_CAPTEURS
        ]

    if "from interventions" in normalized and "count(*)" in normalized and "statut != 'terminé'" in normalized:
        return [{"count": 2}]
    if "from interventions" in normalized and "count(*) as n" in normalized:
        return [{"n": 2}]
    if "from interventions" in normalized and "group by statut" in normalized:
        return [
            {"statut": "DEMANDE", "total": 1, "duree_moy_h": 4.5},
            {"statut": "TECH1_ASSIGNÉ", "total": 1, "duree_moy_h": 2.0},
            {"statut": "TERMINÉ", "total": 1, "duree_moy_h": 8.0},
        ]
    if "from interventions i join capteurs c" in normalized:
        return [
            {
                "id": 10,
                "capteur": "CAP-AIR-002",
                "statut": "DEMANDE",
                "priorite": "URGENTE",
                "description": "Capteur hors service",
                "date_creation": "2026-04-22",
                "ia_approuvee": None,
            }
        ]

    if "from citoyens" in normalized and "count(*) as n" in normalized:
        return [{"n": len(_MOCK_CITOYENS)}]
    if "from citoyens c left join zones z" in normalized:
        return [
            {
                "nom": row["nom"],
                "prenom": row["prenom"],
                "zone": next(zone["nom"] for zone in _MOCK_ZONES if zone["id"] == row["zone_id"]),
                "score_ecolo": row["score_ecolo"],
            }
            for row in _MOCK_CITOYENS
        ]

    if "from vehicules" in normalized and "count(*) as n" in normalized:
        return [{"n": len(_MOCK_VEHICULES)}]
    if "from vehicules" in normalized and "count(*)" in normalized and "statut='en_panne'" in normalized:
        return [{"count": 1}]

    if "from alertes" in normalized and "count(*) as n" in normalized:
        return [{"n": 1}]
    if "from alertes" in normalized and "count(*)" in normalized and "severity='critical'" in normalized:
        return [{"count": 1}]

    if "from mesures m" in normalized and "avg(m.pm25)" in normalized:
        return _MOCK_MESURES
    if "from mesures" in normalized and ("time_bucket" in normalized or "date_trunc" in normalized):
        return [
            {"heure": "2026-04-20T08:00:00", "valeur": 28.1},
            {"heure": "2026-04-20T09:00:00", "valeur": 30.4},
            {"heure": "2026-04-20T10:00:00", "valeur": 27.9},
        ]
    if "from mesures m" in normalized and "count(distinct z.nom)" in normalized:
        return [{"count": 2}]

    if "from fsm_states" in normalized:
        return [{"state": "ACTIF"}]
    if "from fsm_history" in normalized:
        return [
            {
                "from_state": "INACTIF",
                "event": "installation",
                "to_state": "ACTIF",
                "triggered_at": "2026-04-20T08:00:00",
                "triggered_by": "system:test",
            }
        ]

    if "from trajets" in normalized and "count(*) as n" in normalized:
        return [{"n": 4}]

    return []


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def mock_execute_query(monkeypatch):
    monkeypatch.setattr("database.connection.execute_query", _mock_execute_query)
    try:
        import ai.context_builder as context_builder

        monkeypatch.setattr(context_builder, "execute_query", _mock_execute_query)
    except Exception:
        pass
    try:
        import fsm.persistence as persistence

        monkeypatch.setattr(persistence, "execute_query", _mock_execute_query)
    except Exception:
        pass
    yield _mock_execute_query


@pytest.fixture(scope="session")
def pipeline():
    from compiler.pipeline import NLToSQLPipeline

    return NLToSQLPipeline()


@pytest.fixture(scope="session")
def sensor_fsm():
    from fsm.sensor_fsm import SensorLifecycleFSM

    return SensorLifecycleFSM()


@pytest.fixture(scope="session")
def intervention_fsm():
    from fsm.intervention_fsm import InterventionWorkflowFSM

    return InterventionWorkflowFSM(
        ai_advisor_fn=lambda ctx: {
            "approved": True,
            "confidence": 0.99,
            "reason": "Mock approval",
        }
    )


@pytest.fixture(scope="session")
def vehicle_fsm():
    from fsm.vehicle_fsm import VehicleRouteFSM

    return VehicleRouteFSM()
